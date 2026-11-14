from django.conf import settings
from django.urls import path

from . import views

urlpatterns = [
    path('', views.getIndex),
    path('morph', views.index, name='index'),
    path('morph/animegan', views.animegan, name='anime_gan'),
    path('morph/upload', views.uploadMorphImage),
    path('morph/status/<uuid:morph_uuid>/', views.morph_status, name='morph_status'),
    path('morph/log', views.logClientSideMorphError),
]

# Apple Sign-In endpoints. Routed to a 501 kill switch until
# APPLE_SIGN_IN_ENABLED is true (i.e. APPLE_CLIENT_ID / APPLE_CLIENT_SECRET
# are configured on the server).
if settings.APPLE_SIGN_IN_ENABLED:
    urlpatterns += [
        path('morph/exchange_auth_code', views.exchange_auth_code),
        path('morph/user_data', views.user_data),
        path('morph/mymorphs', views.get_user_morphs),
        path('morph/delete_account', views.delete_account, name='delete_account'),
        path('morph/refresh_token', views.refresh_token, name='refresh_token'),
    ]
else:
    urlpatterns += [
        path('morph/exchange_auth_code', views.authDisabled),
        path('morph/user_data', views.authDisabled),
        path('morph/mymorphs', views.authDisabled),
        path('morph/delete_account', views.authDisabled, name='delete_account'),
        path('morph/refresh_token', views.authDisabled, name='refresh_token'),
    ]

urlpatterns += [
    path('facemorphs/<str:filename>', views.serve_morph_image, name='serve_morph_image'),
]
