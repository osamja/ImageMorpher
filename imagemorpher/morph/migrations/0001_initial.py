# Generated by Django 3.2.18 on 2023-05-04 03:28

import django.core.validators
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Morph',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('cancelled', 'Cancelled'), ('deleted', 'Deleted')], default='pending', max_length=10)),
                ('first_image_ref', models.CharField(max_length=100)),
                ('second_image_ref', models.CharField(max_length=100)),
                ('morphed_image_ref', models.CharField(max_length=100)),
                ('morphed_image_filepath', models.CharField(max_length=100)),
                ('is_morph_sequence', models.BooleanField(default=False)),
                ('step_size', models.IntegerField(default=20, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(101)])),
                ('duration', models.IntegerField(default=250, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10000)])),
                ('morph_sequence_time', models.FloatField(default=0.5, validators=[django.core.validators.MinValueValidator(0.01), django.core.validators.MaxValueValidator(1)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]