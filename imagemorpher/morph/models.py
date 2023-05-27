from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.conf import settings
import uuid

class Morph(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('deleted', 'Deleted')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    first_image_ref = models.CharField(max_length=100)
    second_image_ref = models.CharField(max_length=100)
    morphed_image_ref = models.CharField(max_length=100) # uri
    morphed_image_filepath = models.CharField(max_length=100) # filepath
    is_morph_sequence = models.BooleanField(default=False)
    step_size = models.IntegerField(default=20, validators=[MinValueValidator(1), MaxValueValidator(101)])
    duration = models.IntegerField(default=250, validators=[MinValueValidator(1), MaxValueValidator(10000)])
    morph_sequence_time = models.FloatField(default=0.5, validators=[MinValueValidator(0.01), MaxValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    client_id = models.CharField(max_length=100, default='default')

    def __str__(self):
        return f"Morph {self.id}: {self.status}"

    # print the morph object
    def print(self):
        print(f"Morph Status {self.id}: {self.status}")
        print(f"First Image: {self.first_image_ref}")
        print(f"Second Image: {self.second_image_ref}")
        print(f"Morphed Image: {self.morphed_image_ref}")
        print(f"Is Morph Sequence: {self.is_morph_sequence}")
        print(f"Step Size: {self.step_size}")
        print(f"Duration: {self.duration}")
        print(f"Morph Sequence Time: {self.morph_sequence_time}")
        print(f"Created At: {self.created_at}")
        print(f"Updated At: {self.updated_at}")
        print(f"Client Id: {self.client_id}")
        print(f"User: {self.user}")

class Upload(models.Model):
    UPLOAD_STATUS_CHOICES = (
        ('S', 'Success'),
        ('F', 'Failure'),
        ('P', 'Pending'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploads')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=UPLOAD_STATUS_CHOICES)
    error_message = models.TextField(blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)
    morph = models.ForeignKey(Morph, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploads')
    
    def __str__(self):
        return f'Upload {self.id}: {self.status} by {self.user.username} at {self.timestamp}'
