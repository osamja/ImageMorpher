from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.core import serializers
from django.conf import settings
from django.utils.html import escape

import datetime
from pytz import timezone
import json
import pdb
import skimage.io as skio
from .morph import morph
import base64
import io
from PIL import Image
import sys
# morph is essentially the src root directory in this file now
#   aka import all files with morph/<file-path>
sys.path.insert(0, '/app/imagemorpher/morph')

import logging
logger = logging.getLogger(__name__)

# logging.basicConfig(filename='morph/logs/morph-app.log', level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

def isRequestValid(request, Authorization='ImageMorpherV1'):
    try:
        isValidApiKey = request.headers['Authorization'] == Authorization
        formData = request.FILES
        isImg1 = formData['Image-1']
        isImg2 = formData['Image-2']
        if (isValidApiKey and isImg1 and isImg2):
            return True
        return False
    except:
        return False

@api_view(["POST"])
def index(request):
    # pdb.set_trace()
    if not isRequestValid(request):
        logging.info('request is not valid')
        return HttpResponse('Unauthorized', status=401)
    formData = request.FILES
    # pdb.set_trace()
    img1 = skio.imread(formData['Image-1'])
    img2 = skio.imread(formData['Image-2'])

    # In case img is a PNG with a 4th transparency layer, remove this layer
    # This is pretty hacky and may cause bugs; investigate later
    img1 = img1[:, :, :3]
    img2 = img2[:, :, :3] 

    # img1 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/obama_small.jpg')
    # img2 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/george_small.jpg')
    
    try:
        log_message = str(datetime.datetime.now(timezone('UTC'))) + ': Morphing images' 
        logging.info(log_message)
        morphed_img_uri = morph(img1, img2, 0.5)
        return Response(morphed_img_uri)
    except Exception as e:
        logging.error('Error %s', exc_info=e)
        raise
    return Response('Sorry, there was an error processing your reqest')

@api_view(["POST"])
def logClientSideMorphError(request):
    # @TODO: Improve logging here
    logMessage = 'Client side error: ', str(request.body)
    logging.info(str(logMessage))
    return Response('front end error')

@api_view(["GET"])
def getIndex(request):
    return Response('GET /morph')
