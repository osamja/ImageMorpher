from django.urls import path

from . import views

urlpatterns = [
    path('', views.getIndex),
    path('morph', views.index, name='index'),
    path('morph/log', views.logClientSideMorphError),
]
