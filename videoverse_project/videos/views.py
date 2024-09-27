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


