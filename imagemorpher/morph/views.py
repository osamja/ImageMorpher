from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core import serializers
from django.core.exceptions import RequestDataTooBig
from django.conf import settings
from django.utils.html import escape

# from django_dramatiq.middleware import DramatiqMiddleware
from .utils.graphics import getCroppedImagePath
from .utils.image_sources import getMorphUri

from .tasks import processMorph

from exceptions.CropException import CropException

import logging
logger = logging.getLogger(__name__)

# logging.basicConfig(filename='morph/logs/morph-app.log', level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

def isRequestValid(request, Authorization='ImageMorpherV1'):
    try:
        isValidApiKey = request.headers['Authorization'] == Authorization
        formData = request.FILES or request.POST
        isImg1 = formData['firstImageRef']
        isImg2 = formData['secondImageRef']
        push_token = request.POST.get('expoPushToken')
        is_async = request.POST.get('isAsync')

        if push_token and not push_token.startswith('ExponentPushToken'):
            push_token = None
            logging.info('push token is not valid')
            print('push token is not valid')
            return False

        if (isValidApiKey and isImg1 and isImg2):
            return True
        return False
    except:
        return False

@api_view(["POST"])
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

    # duration of each frame in gif in milliseconds
    # if stepSize is small, there will be many frames, so the duration of each frame should be smaller
    duration = request.POST.get('duration')
    duration = int(duration) if duration != None else 250

    morphSequenceTime = request.POST.get('t')
    morphSequenceTime = float(morphSequenceTime) if morphSequenceTime != None else 0.5

    try:
        forwarded_host = request.headers.get('X-Forwarded-Host')
        morph_uri, morph_filepath = getMorphUri(forwarded_host, isMorphSequence)

        if not is_async:
            processMorph(isMorphSequence, stepSize, duration, img1_path, img2_path, morphSequenceTime, morph_uri, morph_filepath)
            return Response(morph_uri, status=status.HTTP_200_OK)
        else:
            processMorph.send(isMorphSequence, stepSize, duration, img1_path, img2_path, morphSequenceTime, morph_uri, morph_filepath, push_token)
            morphResponse = {
                'title': 'Morphing',
                'body': 'Your morph is being processed',
                'morphUri': morph_uri,
            }
            return Response(morphResponse, status=status.HTTP_200_OK)
    except Exception as e:
        logging.error('Error %s', exc_info=e)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def logClientSideMorphError(request):
    # @TODO: Improve logging here
    logMessage = 'Client side error: ', str(request.body)
    logging.info(str(logMessage))
    return Response('front end error')

@api_view(["POST"])
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

@api_view(["GET"])
def getIndex(request):
    return Response('GET /morph')
