from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.contrib import messages

from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
# from django.core import serializers
from django.contrib.auth.models import User
from django.core.exceptions import RequestDataTooBig
from django.conf import settings
from django.utils.html import escape
import uuid

from .models import Morph, Upload

import requests

# from django_dramatiq.middleware import DramatiqMiddleware
from .utils.graphics import getCroppedImagePath
from .utils.image_sources import getMorphUri, getMorphFilename

from .tasks import processMorph

from exceptions.CropException import CropException
from exceptions.FaceDetectException import FaceDetectException

import logging
logger = logging.getLogger(__name__)

from apple_auth import AppleSignInAuthentication

import os
from dotenv import load_dotenv

# load root .env file
load_dotenv(dotenv_path='../../.env')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

@api_view(['GET'])
@authentication_classes([AppleSignInAuthentication])
@permission_classes([IsAuthenticated])
def user_data(request):
    """
    Function to provide User Data
    """
    # return 401 for testing that a refresh token is revoked
    # return Response({"detail": "testing revoke of refresh token"}, status=401)
    if request.user.is_authenticated:
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    else:
        return Response({"detail": "Invalid or expired token"}, status=403)
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    print("delete account")

    CLIENT_ID = os.environ.get('APPLE_CLIENT_ID')
    CLIENT_SECRET = os.environ.get('APPLE_CLIENT_SECRET')

    # Extract refresh token from request header X_Refresh_Token
    refresh_token = request.headers.get("X-REFRESH-TOKEN", None)

    # If refresh token is not provided, return error response
    if refresh_token is None:
        return Response({"detail": "Refresh token not provided"}, status=status.HTTP_400_BAD_REQUEST)

    # Prepare the headers and body for the revoke token request
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
        'token': refresh_token,
        'token_type_hint': 'refresh_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    # Send request to Apple's Revoke Token API
    response = requests.post('https://appleid.apple.com/auth/revoke', headers=headers, data=data)

    # Check response from Apple's API
    if response.status_code == 200:
        # If the revoke was successful, delete the user's account
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        # If the revoke was not successful, return error response
        return Response({"detail": "Failed to revoke token"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([AllowAny])
def exchange_auth_code(request):
    Apple_Sign_In_Auth = AppleSignInAuthentication()
    authorization_code = request.data.get('authorizationCode')

    if not authorization_code:
        return Response({"detail": "Authorization code not provided"}, status=400)

    try:
        jwt_token = Apple_Sign_In_Auth.exchange_auth_code_for_token(authorization_code)
    except Exception as e:
        return Response({"detail": str(e)}, status=500)

    return JsonResponse(jwt_token)

@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    Apple_Sign_In_Auth = AppleSignInAuthentication()
    refresh_token = request.data.get('refresh_token')

    if not refresh_token:
        return Response({"detail": "Refresh token not provided"}, status=400)

    try:
        new_id_token = Apple_Sign_In_Auth.exchange_refresh_token_for_id_token(refresh_token)
    except Exception as e:
        return Response({"detail": str(e)}, status=500)

    return JsonResponse(new_id_token)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_morphs(request):
    morphs = Morph.objects.filter(user=request.user)
    morph_ids = [morph.id for morph in morphs]
    response = {
        'morph_ids': morph_ids
    }

    return JsonResponse(response)

def isRequestValid(request, Authorization='ImageMorpherV1'):
    try:
        formData = request.FILES or request.POST
        isImg1 = formData['firstImageRef']
        isImg2 = formData['secondImageRef']
        push_token = request.POST.get('expoPushToken')

        if push_token and not push_token.startswith('ExponentPushToken'):
            push_token = None
            logging.info('push token is not valid')
            print('push token is not valid')
            return False

        if (isImg1 and isImg2):
            return True
        return False
    except:
        return False

@api_view(["POST"])
# @permission_classes([IsAuthenticated])
def index(request):
    formData = request.FILES or request.POST
    print('morph request received')
    if not isRequestValid(request):
        morphResponse = {
            'title': 'Invalid Request',
            'body': 'Request is not valid',
        }

        return Response(morphResponse, status=status.HTTP_401_FORBIDDEN)

    img1_path = formData['firstImageRef']       # e.g. 2021-07-31-18-46-33-232174-b19ac14523fb4f5fb69dafa86ff97e6f.jpg
    img2_path = formData['secondImageRef']      #

    push_token = request.POST.get('expoPushToken')

    is_async = request.POST.get('isAsync')
    is_async = True if is_async == 'True' else False      # TODO: Use async by default (by June 2023)
    
    isMorphSequence = request.POST.get('isSequence')
    isMorphSequence = True if isMorphSequence == 'True' else False

    stepSize = request.POST.get('stepSize')
    stepSize = int(stepSize) if stepSize != None else 20

    clientId = request.POST.get('clientId')
    clientId = clientId if clientId != None else 'default'

    # duration of each frame in gif in milliseconds
    # if stepSize is small, there will be many frames, so the duration of each frame should be smaller
    duration = request.POST.get('duration')
    duration = int(duration) if duration != None else 250

    morphSequenceTime = request.POST.get('t')
    morphSequenceTime = float(morphSequenceTime) if morphSequenceTime != None else 0.5

    morph_instance = None

    user = None
    if request.user.is_authenticated:
        user = request.user
    
    try:
        morph_id = uuid.uuid4()
        morph_filename = getMorphFilename(morph_id)
        forwarded_host = request.headers.get('X-Forwarded-Host')
        morph_uri, morph_filepath = getMorphUri(forwarded_host, morph_filename, isMorphSequence)

        # Create a new Morph instance
        morph_instance = Morph(
            id=morph_id,
            status='pending',  # or any other initial status you'd like
            user=user,
            first_image_ref=img1_path,
            second_image_ref=img2_path,
            morphed_image_ref=morph_uri,
            morphed_image_filepath=morph_filepath,
            is_morph_sequence=isMorphSequence,
            step_size=stepSize,
            duration=duration,
            morph_sequence_time=morphSequenceTime,
            client_id=clientId,
        )

        morph_instance.save()

        morph_id_str = str(morph_id)

        if not is_async:
            processMorph(morph_id_str)
            return Response(morph_uri, status=status.HTTP_200_OK)
        else:
            processMorph.send(morph_id_str, push_token)
            morphResponse = {
                'title': 'Morphing',
                'body': 'Your morph is being processed',
                'morphUri': morph_uri,
                'morphId': morph_id_str,
            }
            return Response(morphResponse, status=status.HTTP_200_OK)
    except Exception as e:
        # mark morph as failed
        if morph_instance:
            morph_instance.status = 'failed'
            morph_instance.save()
        logging.error('Error %s', exc_info=e)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def logClientSideMorphError(request):
    logMessage = request.body
    print(logMessage)
    logging.info(str(logMessage))
    return Response(status=status.HTTP_200_OK)

@api_view(["POST"])
# @permission_classes([IsAuthenticated])
def uploadMorphImage(request):

    # user = request.user if request.user.is_authenticated else None

    # Create an Upload instance at the start of the request
    # upload = Upload.objects.create(user=user, status='P')

    # upload = Upload(user=user, status='P')

    try:
        formData = request.FILES or request.POST
        img = formData.get('firstImageRef', False)

        # Save file_type and file_size to Upload instance
        # upload.file_type = img.content_type
        # upload.file_size = img.size
        # upload.save()

        cropped_img_path = getCroppedImagePath(img)
    except CropException as e:
        logging.error(e)
        errorMessage = str(e)

        # Update Upload instance with error message
        # upload.error_message = errorMessage
        # upload.status = 'F'
        # upload.save()

        return Response(errorMessage, status=422)
    except FaceDetectException as e:
        logging.error(e)
        errorMessage = str(e)

        # Update Upload instance with error message
        # upload.error_message = errorMessage
        # upload.status = 'F'
        # upload.save()

        return Response(errorMessage, status=422)
    except RequestDataTooBig as e:
        logging.error(e)
        errorMessage = 'Image too large'

        # Update Upload instance with error message
        # upload.error_message = errorMessage
        # upload.status = 'F'
        # upload.save()

        return Response(errorMessage, status=422)
    except Exception as e:
        logging.error(e)
        errorMessage = 'Could not crop image'

        # Update Upload instance with error message
        # upload.error_message = errorMessage
        # upload.status = 'F'
        # upload.save()

        return Response(errorMessage, status=422)

    # If the image cropping succeeds, update the status of the Upload instance to Success
    # upload.status = 'S'
    # upload.save()

    return Response(cropped_img_path)

def morph_status(request, morph_uuid):
    try:
        morph = Morph.objects.get(pk=morph_uuid)
    except Morph.DoesNotExist:
        raise Http404("Morph not found")

    status_data = {
        'status': morph.status,
        'morphUri': morph.morphed_image_ref,
    }

    return JsonResponse(status_data)

@api_view(["GET"])
def getIndex(request):
    return Response('GET /morph')
