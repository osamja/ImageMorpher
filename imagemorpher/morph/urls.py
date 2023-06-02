from django.urls import path

from . import views

urlpatterns = [
    path('', views.getIndex),
    path('morph', views.index, name='index'),
    path('morph/animegan', views.animegan, name='anime_gan'),
    path('morph/upload', views.uploadMorphImage),
    path('morph/status/<uuid:morph_uuid>/', views.morph_status, name='morph_status'),
    path('morph/log', views.logClientSideMorphError),
    path('morph/exchange_auth_code', views.exchange_auth_code),
    path('morph/user_data', views.user_data),
    path('morph/mymorphs', views.get_user_morphs),
    path('morph/delete_account', views.delete_account, name='delete_account'),
    path('morph/refresh_token', views.refresh_token, name='refresh_token'),
]
