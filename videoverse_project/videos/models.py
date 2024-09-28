from django.db import models

class Video(models.Model):
    file = models.FileField(upload_to='videos/')
    duration = models.FloatField(null=True)  # Duration in seconds
    size = models.BigIntegerField(null=True)  # Size in bytes
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title
