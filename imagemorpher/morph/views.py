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

@api_view(["POST"])
def index(request):
    formData = request.FILES
    # img1 = skio.imread(formData['Image-1'])
    # img2 = skio.imread(formData['Image-2'])
    img1 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/obama_small.jpg')
    img2 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/george_small.jpg')
    
    morphed_img_path = morph(img1, img2, 0.5)
    try:
        return Response(morphed_img_path)
    except IOError:
        raise
        return Response('error bro')
    return Response("Hello", content_type="image/jpeg")

@api_view(["GET"])
def getMorphedImage(request):
    return Response('get morphed image')
