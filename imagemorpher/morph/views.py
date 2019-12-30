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
import json
import pdb
import skimage.io as skio
from .main_morph import morph
import base64
import io
from PIL import Image

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
    if not isRequestValid(request):
        return HttpResponse('Unauthorized', status=401)
    formData = request.FILES
    img1 = skio.imread(formData['Image-1'])
    img2 = skio.imread(formData['Image-2'])
    # img1 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/obama_small.jpg')
    # img2 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/george_small.jpg')
    
    morphed_img_uri = morph(img1, img2, 0.5)
    try:
        return Response(morphed_img_uri)
    except IOError:
        raise
        return Response('error bro')
    return Response('wut wut')

@api_view(["GET"])
def getIndex(request):
    return Response('GET /morph')
