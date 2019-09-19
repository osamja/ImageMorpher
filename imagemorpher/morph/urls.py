from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('temp_morphed_images/*', views.getMorphedImage, name='getMorphedImage'),
]
