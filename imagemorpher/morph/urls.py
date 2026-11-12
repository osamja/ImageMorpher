from django.urls import path

from . import views

urlpatterns = [
    path('', views.getIndex),
    path('morph', views.index, name='index'),
    path('morph/animegan', views.animegan, name='anime_gan'),
    path('morph/upload', views.uploadMorphImage),
    path('morph/status/<uuid:morph_uuid>/', views.morph_status, name='morph_status'),
    path('morph/log', views.logClientSideMorphError),
    # Apple Sign-In is temporarily disabled: APPLE_CLIENT_ID and
    # APPLE_CLIENT_SECRET are not configured on this server. Anonymous
    # morphing is unaffected. Re-point these to the real views when ready.
    path('morph/exchange_auth_code', views.authDisabled),
    path('morph/user_data', views.authDisabled),
    path('morph/mymorphs', views.authDisabled),
    path('morph/delete_account', views.authDisabled, name='delete_account'),
    path('morph/refresh_token', views.authDisabled, name='refresh_token'),
    path('facemorphs/<str:filename>', views.serve_morph_image, name='serve_morph_image'),
]
