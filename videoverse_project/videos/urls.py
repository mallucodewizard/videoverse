from django.urls import path
from .views import upload_video,trim_video,merge_videos

urlpatterns = [
    path('upload/', upload_video, name='upload_video'),
    path('trim/<int:pk>/', trim_video, name='trim_video'),
    path('merge/', merge_videos, name='merge_videos'),
]
