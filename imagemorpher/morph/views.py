from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render
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

from .models import Morph

# from django_dramatiq.middleware import DramatiqMiddleware
from .utils.graphics import getCroppedImagePath
from .utils.image_sources import getMorphUri, getMorphFilename

from .tasks import processMorph

from exceptions.CropException import CropException

import logging
logger = logging.getLogger(__name__)

from apple_auth import AppleSignInAuthentication

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
    if request.user.is_authenticated:
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    else:
        return Response({"detail": "Invalid or expired token"}, status=403)

@api_view(["POST"])
@permission_classes([AllowAny])
def exchange_auth_code(request):
    Apple_Sign_In_Auth = AppleSignInAuthentication()
    authorization_code = request.data.get('authorizationCode')

    if not authorization_code:
        return Response({"detail": "Authorization code not provided"}, status=400)

    try:
        id_token = Apple_Sign_In_Auth.exchange_auth_code_for_token(authorization_code)
    except Exception as e:
        return Response({"detail": str(e)}, status=500)

    return JsonResponse(id_token)

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

    try:
        morph_id = uuid.uuid4()
        morph_filename = getMorphFilename(morph_id)
        forwarded_host = request.headers.get('X-Forwarded-Host')
        morph_uri, morph_filepath = getMorphUri(forwarded_host, morph_filename, isMorphSequence)

        # Create a new Morph instance
        morph_instance = Morph(
            id=morph_id,
            status='pending',  # or any other initial status you'd like
            user=request.user,
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
    try:
        formData = request.FILES or request.POST
        img = formData.get('firstImageRef', False)
        cropped_img_path = getCroppedImagePath(img)
    except CropException as e:
        logging.error(e)
        errorMessage = str(e)
        return Response(errorMessage, status=422)
    except RequestDataTooBig as e:
        logging.error(e)
        errorMessage = 'Image too large'
        return Response(errorMessage, status=422)
    except Exception as e:
        logging.error(e)
        errorMessage = 'Could not crop image'
        return Response(errorMessage, status=422)

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
