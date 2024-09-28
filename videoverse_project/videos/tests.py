from django.test import TestCase
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Video
import time
import os
import moviepy.editor as mp

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class VideoUploadTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_video_upload(self):
        print("Starting test_video_upload")
        video_path = os.path.join(project_path, 'media', 'videos', '2637-161442811_small.mp4')
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
        video_file = SimpleUploadedFile("test_video.mp4", video_data, content_type="video/mp4")
        response = self.client.post('/api/videos/upload/', {'file': video_file, 'title': 'Test Video'})
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.data)
        self.assertIn('title', response.data)
        self.assertEqual(response.data['title'], 'Test Video')
        print("Finished test_video_upload")

    def test_video_upload_invalid_file(self):
        print("Starting test_video_upload_invalid_file")
        invalid_file = SimpleUploadedFile("invalid.txt", b"file_content", content_type="text/plain")
        response = self.client.post('/api/videos/upload/', {'file': invalid_file, 'title': 'Invalid Video'})
        self.assertEqual(response.status_code, 400)
        print("Finished test_video_upload_invalid_file")

    def test_video_upload_missing_title(self):
        print("Starting test_video_upload_missing_title")
        video_path = os.path.join(project_path, 'media', 'videos', '2637-161442811_small.mp4')
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
        video_file = SimpleUploadedFile("test_video.mp4", video_data, content_type="video/mp4")
        response = self.client.post('/api/videos/upload/', {'file': video_file})
        self.assertEqual(response.status_code, 400)
        print("Finished test_video_upload_missing_title")

class VideoModelTestCase(TestCase):
    def test_video_creation(self):
        print("Starting test_video_creation")
        video_path = os.path.join(project_path, 'media', 'videos', '2637-161442811_small.mp4')
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
        video_file = SimpleUploadedFile("test_video.mp4", video_data, content_type="video/mp4")
        video = Video.objects.create(title="Test Video", file=video_file)
        self.assertEqual(video.title, "Test Video")
        self.assertTrue(video.file)
        print("Finished test_video_creation")

class VideoAccessTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        video_path = os.path.join(project_path, 'media', 'videos', '2637-161442811_small.mp4')
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
        video_file = SimpleUploadedFile("test_video.mp4", video_data, content_type="video/mp4")
        self.video = Video.objects.create(title="Test Video", file=video_file)

    def test_generate_shareable_link(self):
        print("Starting test_generate_shareable_link")
        response = self.client.post(f'/api/videos/share/{self.video.id}/', {'expiry_time': 3})
        self.assertEqual(response.status_code, 200)
        self.assertIn('shareable_link', response.data)
        print("Finished test_generate_shareable_link")

    def test_access_shared_video(self):
        print("Starting test_access_shared_video")
        response = self.client.post(f'/api/videos/share/{self.video.id}/')
        self.assertEqual(response.status_code, 200)
        shareable_link = response.data['shareable_link']
        response = self.client.get(shareable_link)
        self.assertEqual(response.status_code, 200)
        self.assertIn('video_url', response.data)
        print("Finished test_access_shared_video")

    def test_access_shared_video_expired(self):
        print("Starting test_access_shared_video_expired")
        response = self.client.post(f'/api/videos/share/{self.video.id}/')
        self.assertEqual(response.status_code, 200)
        shareable_link = response.data['shareable_link']
        print("Waiting for the link to expire...")
        time.sleep(7)  # Wait for the link to expire
        response = self.client.get(shareable_link)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Link has expired.')
        print("Finished test_access_shared_video_expired")

class VideoE2ETestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        video_path = os.path.join(project_path, 'media', 'videos', '2637-161442811_small.mp4')
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
        video_file = SimpleUploadedFile("test_video.mp4", video_data, content_type="video/mp4")
        self.video = Video.objects.create(title="Test Video", file=video_file)

    def test_full_video_upload_and_access_flow(self):
        print("Starting test_full_video_upload_and_access_flow")
        video_path = os.path.join(project_path, 'media', 'videos', '2637-161442811_small.mp4')
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
        video_file = SimpleUploadedFile("test_video.mp4", video_data, content_type="video/mp4")

        # Step 1: Upload a video
        print("Uploading video...")
        upload_response = self.client.post('/api/videos/upload/', {'file': video_file, 'title': 'E2E Test Video'})
        self.assertEqual(upload_response.status_code, 201)
        video_id = upload_response.data['id']

        # Step 2: Generate a shareable link
        print("Generating shareable link...")
        link_response = self.client.post(f'/api/videos/share/{video_id}/', {'expiry_time': 3})
        self.assertEqual(link_response.status_code, 200)
        shareable_link = link_response.data['shareable_link']

        # Step 3: Access the video using the shareable link
        print("Accessing video using shareable link...")
        access_response = self.client.get(shareable_link)
        self.assertEqual(access_response.status_code, 200)
        self.assertIn('video_url', access_response.data)
        print("Finished test_full_video_upload_and_access_flow")

    def test_video_merge(self):
        print("Starting test_video_merge")
        video_path1 = os.path.join(project_path, 'media', 'videos', '2637-161442811_small.mp4')
        video_path2 = os.path.join(project_path, 'media', 'videos', '9245420-uhd_1440_2068_30fps_7VkN46f.mp4')
        with open(video_path1, 'rb') as video_file1, open(video_path2, 'rb') as video_file2:
            video_data1 = video_file1.read()
            video_data2 = video_file2.read()
        video_file1 = SimpleUploadedFile("test_video1.mp4", video_data1, content_type="video/mp4")
        video_file2 = SimpleUploadedFile("test_video2.mp4", video_data2, content_type="video/mp4")

        # Upload both videos
        response1 = self.client.post('/api/videos/upload/', {'file': video_file1, 'title': 'Test Video 1'})
        response2 = self.client.post('/api/videos/upload/', {'file': video_file2, 'title': 'Test Video 2'})
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response2.status_code, 201)
        video_id1 = response1.data['id']
        video_id2 = response2.data['id']

        # Merge videos
        merge_response = self.client.post('/api/videos/merge/', {'video_ids': [video_id1, video_id2]})
        self.assertEqual(merge_response.status_code, 200)
        self.assertIn('merged_video_url', merge_response.data)
        print("Finished test_video_merge")

    def test_video_trim(self):
        print("Starting test_video_trim")
        video_path = os.path.join(project_path, 'media', 'videos', '2637-161442811_small.mp4')
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
        video_file = SimpleUploadedFile("test_video.mp4", video_data, content_type="video/mp4")

        # Upload video
        upload_response = self.client.post('/api/videos/upload/', {'file': video_file, 'title': 'Test Video'})
        self.assertEqual(upload_response.status_code, 201)
        video_id = upload_response.data['id']

        # Check video duration
        video = mp.VideoFileClip(video_path)
        video_duration = video.duration
        print(f"Video duration: {video_duration} seconds")

        # Trim video
        start_time = 0
        end_time = min(10, video_duration)  # Ensure end_time is within the video duration
        trim_response = self.client.post(f'/api/videos/trim/{video_id}/', {'start_time': start_time, 'end_time': end_time})
        print(f"Trim response status code: {trim_response.status_code}")
        print(f"Trim response data: {trim_response.data}")
        self.assertEqual(trim_response.status_code, 200)
        self.assertIn('trimmed_file', trim_response.data)
        print("Finished test_video_trim")