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
import uuid
import skimage.io as skio
from .morph import morph
import base64
import io
from PIL import Image
import numpy as np
import sys
from skimage import img_as_ubyte
from utils.graphics import getCroppedImages
from utils.image_sources import saveImg

# morph is essentially the src root directory in this file now
#   aka import all files with morph/<file-path>
sys.path.insert(0, '/app/imagemorpher/morph')

import logging
logger = logging.getLogger(__name__)

# logging.basicConfig(filename='morph/logs/morph-app.log', level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

def isRequestValid(request, Authorization='ImageMorpherV1'):
    try:
        isValidApiKey = request.headers['Authorization'] == Authorization
        formData = request.FILES or request.POST
        isImg1 = formData['Image-1']
        isImg2 = formData['Image-2']
        if (isValidApiKey and isImg1 and isImg2):
            return True
        return False
    except:
        return False

def getMorphedImgUri(img1, img2, t):
    try:
        log_message = str(datetime.datetime.now(timezone('UTC'))) + ': Morphing images' 
        logging.info(log_message)
        morphed_img_filename, morphed_im = morph(img1, img2, t)
        return morphed_img_filename, morphed_im
    except Exception as e:
        logging.error('Error %s', exc_info=e)
        raise

@api_view(["POST"])
def index(request):
    # pdb.set_trace()
    formData = request.FILES or request.POST

    if not isRequestValid(request):
        logging.info('request is not valid')
        return HttpResponse('Invalid Request', status=401)

    img1, img2 = getCroppedImages(formData['Image-1'], formData['Image-2'])
    img1_path = saveImg(img1)
    img2_path = saveImg(img2)

    # img1 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/obama_small.jpg')
    # img2 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/george_small.jpg')
    
    isMorphSequence = request.POST.get('isSequence')
    isMorphSequence = True if isMorphSequence == 'True' else False

    stepSize = request.POST.get('stepSize')
    stepSize = int(stepSize) if stepSize != None else 20

    # duration for gif, the smaller the step size the smaller the duration that each frame in the 
    # gif will be displayed
    duration = 500 # temporary value which may be adjusted

    morphSequenceTime = request.POST.get('t')
    morphSequenceTime = float(morphSequenceTime) if morphSequenceTime != None else 0.5
    
    if (isMorphSequence):
        morphed_img_uri_list = []
        for i in range(0, 101, stepSize):
            if i == 0:
                morphed_img_uri_list.append((img1_path, img1)) # return src img
                continue
            if i >= 100:
                morphed_img_uri_list.append((img2_path, img2)) # return dest img
                continue
            t = float(i / 100) or 0
            _img1 = np.copy(img1)
            _img2 = np.copy(img2)
            morphed_img_filename, morphed_im = getMorphedImgUri(_img1, _img2, t)
            morphed_img_uri_list.append((morphed_img_filename, morphed_im))
        
        fileHash = uuid.uuid4()
        morphDate = str(datetime.date.today())
        gif_filename = morphDate + fileHash.hex + '.gif'
        morphed_gif_path = 'morph/content/temp_morphed_images/' + gif_filename    # location of saved image
        morphed_gif_uri = 'https://sammyjaved.com/facemorphs/' + gif_filename     # /facemorphs directory serves static content via nginx

        morphed_im_list = []
        for i, im in enumerate(morphed_img_uri_list):
            if i == 0:
                # load the uploaded img in memory
                morphed_im_filename = 'morph/content/temp_morphed_images/' + im[0]
                morphed_im = Image.open(morphed_im_filename)
                morphed_im_list.append(morphed_im)
                continue
            if i == len(morphed_img_uri_list) - 1:
                # load uploaded img in memory
                morphed_im_filename = 'morph/content/temp_morphed_images/' + im[0]
                morphed_im = Image.open(morphed_im_filename)
                morphed_im_list.append(morphed_im)
                continue

            morphed_im_filename = 'morph/content/temp_morphed_images/' + im[0]
            morphed_im = Image.open(morphed_im_filename)
            morphed_im_list.append(morphed_im)
        first_image = morphed_im_list[0]
        appended_images = morphed_im_list[1:]
        first_image.save(morphed_gif_path, save_all=True, append_images=appended_images, loop=0, duration=duration)
        return Response(morphed_gif_uri)
    else:
        morphed_img_filename, morphed_im = getMorphedImgUri(img1, img2, morphSequenceTime)
        morphed_img_uri = 'https://sammyjaved.com/facemorphs/' + morphed_img_filename   
        return Response(morphed_img_uri)

@api_view(["POST"])
def logClientSideMorphError(request):
    # @TODO: Improve logging here
    logMessage = 'Client side error: ', str(request.body)
    logging.info(str(logMessage))
    return Response('front end error')

@api_view(["GET"])
def getIndex(request):
    return Response('GET /morph')
