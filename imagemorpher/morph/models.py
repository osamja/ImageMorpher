from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
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

    # first_image = models.ImageField(upload_to='first_images/')
    # second_image = models.ImageField(upload_to='second_images/')
    # morphed_image = models.ImageField(upload_to='morphed_images/', null=True, blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
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
    def printMorph(self):
        print(f"Morph {self.id}: {self.status}")
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
