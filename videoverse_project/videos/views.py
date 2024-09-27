from rest_framework import status, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from datetime import timedelta, datetime
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.utils import timezone
from .models import Video
from .serializers import VideoSerializer
from moviepy.editor import VideoFileClip,concatenate_videoclips
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

    # Correctly set the output directory
    output_dir = os.path.join(settings.MEDIA_ROOT, "trimmed_videos")
    os.makedirs(output_dir, exist_ok=True)  # Ensure directory exists

    # Fix the output path to avoid duplicate folder names
    trimmed_file_name = f"trimmed_{os.path.basename(video.file.name)}"
    output_path = os.path.join(output_dir, trimmed_file_name)

    try:
        with VideoFileClip(video_path) as clip:
            trimmed_clip = clip.subclip(start_time, end_time)
            trimmed_clip.write_videofile(output_path, codec="libx264")
    except OSError as e:
        return Response({"error": f"FFMPEG error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Return the path to the trimmed video
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
            clip = VideoFileClip(video.file.path)

            # Optionally ensure all clips have the same resolution (you can hardcode resolution)
            clip = clip.resize(height=720)  # Set a uniform height (width will adjust proportionally)

            clips.append(clip)
        except Video.DoesNotExist:
            return Response({"error": f"Video with id {video_id} not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error loading video {video_id}: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        # Safely concatenate clips using 'compose' method
        merged_clip = concatenate_videoclips(clips, method="compose")

        output_dir = os.path.join(settings.MEDIA_ROOT, "merged_videos")
        os.makedirs(output_dir, exist_ok=True)
        # Generate a timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_path = os.path.join(output_dir, f"merged_output{timestamp}.mp4")

        # Write the merged video file
        merged_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    except Exception as e:
        return Response({"error": f"Error merging videos: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"merged_video_url": output_path}, status=status.HTTP_200_OK)


signer = TimestampSigner()

@api_view(['POST'])
def generate_shareable_link(request, video_id):
    try:
        video = Video.objects.get(pk=video_id)
    except Video.DoesNotExist:
        return Response({"error": "Video not found."}, status=status.HTTP_404_NOT_FOUND)

    expiry_time = request.data.get('expiry_time', 10)  # Default
    if not expiry_time:
        return Response({"error": "Expiry time not provided."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Generate a signed URL with the video ID and expiry time
        signed_value = signer.sign_object({"video_id": video_id, "expiry_time": expiry_time})
        shareable_link = f"{request.build_absolute_uri('/api/videos/access/')}{signed_value}/"

        return Response({"shareable_link": shareable_link}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def access_shared_video(request, signed_value):
    try:
        # Validate the signed value
        data = signer.unsign_object(signed_value, max_age=60*60*24)  # 24 hours expiry
        video_id = data.get("video_id")
        # Get expiry_time from request or default to 10 minutes from now
        expiry_time = request.data.get('expiry_time')
        
        if not expiry_time:
            # Default expiry time is 10 minutes from now
            expiry_time = (timezone.now() + timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%S')

        if timezone.now() > timezone.make_aware(timezone.datetime.strptime(expiry_time, '%Y-%m-%dT%H:%M:%S')):
            return Response({"error": "Link has expired."}, status=status.HTTP_400_BAD_REQUEST)

        video = Video.objects.get(pk=video_id)
        video_url = request.build_absolute_uri(video.file.url)

        return Response({"video_url": video_url}, status=status.HTTP_200_OK)

    except SignatureExpired:
        return Response({"error": "Link has expired."}, status=status.HTTP_400_BAD_REQUEST)
    except BadSignature:
        return Response({"error": "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)
    except Video.DoesNotExist:
        return Response({"error": "Video not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
