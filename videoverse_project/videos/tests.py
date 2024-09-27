from django.test import TestCase
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

class VideoUploadTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_video_upload(self):
        with open('path_to_test_video.mp4', 'rb') as video_file:
            response = self.client.post('/api/videos/upload/', {'file': video_file, 'title': 'Test Video'})
        self.assertEqual(response.status_code, 201)
