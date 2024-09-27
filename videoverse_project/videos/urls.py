from django.urls import path
from .views import upload_video,trim_video,merge_videos,generate_shareable_link

urlpatterns = [
    path('upload/', upload_video, name='upload_video'),
    path('trim/<int:pk>/', trim_video, name='trim_video'),
    path('merge/', merge_videos, name='merge_videos'),
    path('share/<int:video_id>/', generate_shareable_link, name='generate_shareable_link'),
    # path('access/<str:signed_value>/', access_shared_video, name='access_shared_video'),
]
