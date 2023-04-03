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
        if (isValidApiKey and isImg1 and isImg2):
            return True
        return False
    except:
        return False

@api_view(["POST"])
def index(request):
    formData = request.FILES or request.POST

    if not isRequestValid(request):
        logging.info('request is not valid')
        return HttpResponse('Invalid Request', status=401)

    img1_path = formData['firstImageRef']       # e.g. 2021-07-31-18-46-33-232174-b19ac14523fb4f5fb69dafa86ff97e6f.jpg
    img2_path = formData['secondImageRef']      #

    push_token = request.POST.get('expoPushToken')
    
    isMorphSequence = request.POST.get('isSequence')
    isMorphSequence = True if isMorphSequence == 'True' else False

    stepSize = request.POST.get('stepSize')
    stepSize = int(stepSize) if stepSize != None else 20

    # duration for gif, the smaller the step size the smaller the duration that each frame in the 
    # gif will be displayed
    duration = 10 # temporary value which may be adjusted

    morphSequenceTime = request.POST.get('t')
    morphSequenceTime = float(morphSequenceTime) if morphSequenceTime != None else 0.5

    try:
        if push_token == None:  # if no push token is provided, then process the morph synchronously
            morph_uri = processMorph(isMorphSequence, stepSize, duration, img1_path, img2_path, morphSequenceTime)
            return Response(morph_uri, status=status.HTTP_200_OK)
        else:   # if a push token is provided, then process the morph asynchronously
            processMorph.send(isMorphSequence, stepSize, duration, img1_path, img2_path, morphSequenceTime, push_token)
        return Response({'Processing morph...'}, status=status.HTTP_200_OK)
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
