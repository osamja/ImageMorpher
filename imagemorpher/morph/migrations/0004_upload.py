# Generated by Django 3.2.18 on 2023-05-25 01:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('morph', '0003_morph_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('S', 'Success'), ('F', 'Failure'), ('P', 'Pending')], max_length=1)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('file_type', models.CharField(blank=True, max_length=50, null=True)),
                ('file_size', models.IntegerField(blank=True, null=True)),
                ('morph', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploads', to='morph.morph')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploads', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
