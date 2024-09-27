from rest_framework import status, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from .models import Video
from .serializers import VideoSerializer
from moviepy.editor import VideoFileClip
import os

# Custom validation limits
MAX_SIZE_MB = 25
MIN_DURATION_SEC = 5
MAX_DURATION_SEC = 25

def validate_video_file(file):
    size_in_mb = file.size / (1024 * 1024)
    if size_in_mb > MAX_SIZE_MB:
        raise serializers.ValidationError("File size exceeds the maximum limit of 25 MB.")

def get_video_duration(file_path):
    with VideoFileClip(file_path) as clip:
        return clip.duration

@api_view(['POST'])
def upload_video(request):
    file = request.FILES.get('file')
    title = request.data.get('title', '')

    if not file:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate file size
    validate_video_file(file)

    # Save file temporarily to validate duration
    temp_file_path = os.path.join(settings.MEDIA_ROOT, file.name)
    with open(temp_file_path, 'wb+') as temp_file:
        for chunk in file.chunks():
            temp_file.write(chunk)

    # Validate video duration
    duration = get_video_duration(temp_file_path)
    if duration < MIN_DURATION_SEC or duration > MAX_DURATION_SEC:
        os.remove(temp_file_path)
        return Response({"error": "Video duration must be between 5 and 25 seconds."}, status=status.HTTP_400_BAD_REQUEST)

    # Save valid video
    video = Video.objects.create(file=file, title=title, duration=duration, size=file.size)
    serializer = VideoSerializer(video)
    os.remove(temp_file_path)  # Clean up temp file

    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def trim_video(request, pk):
    try:
        video = Video.objects.get(pk=pk)
    except Video.DoesNotExist:
        return Response({"error": "Video not found."}, status=status.HTTP_404_NOT_FOUND)

    start_time = float(request.data.get('start_time', 0))
    end_time = float(request.data.get('end_time', video.duration))

    if start_time < 0 or end_time > video.duration or start_time >= end_time:
        return Response({"error": "Invalid start or end time."}, status=status.HTTP_400_BAD_REQUEST)

    video_path = video.file.path
    output_path = os.path.join(settings.MEDIA_ROOT, f"trimmed_{video.file.name}")

    with VideoFileClip(video_path) as clip:
        trimmed_clip = clip.subclip(start_time, end_time)
        trimmed_clip.write_videofile(output_path, codec="libx264")

    # Return path to the trimmed video
    return Response({"trimmed_file": output_path}, status=status.HTTP_200_OK)

@api_view(['POST'])
def merge_videos(request):
    video_ids = request.data.get('video_ids', [])

    if not video_ids:
        return Response({"error": "No video ids provided."}, status=status.HTTP_400_BAD_REQUEST)

    clips = []
    for video_id in video_ids:
        try:
            video = Video.objects.get(pk=video_id)
            clips.append(VideoFileClip(video.file.path))
        except Video.DoesNotExist:
            return Response({"error": f"Video with id {video_id} not found."}, status=status.HTTP_404_NOT_FOUND)

    merged_clip = concatenate_videoclips(clips)
    output_path = os.path.join(settings.MEDIA_ROOT, "merged_output.mp4")
    merged_clip.write_videofile(output_path, codec="libx264")

    return Response({"merged_video_url": output_path}, status=status.HTTP_200_OK)
