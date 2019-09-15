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

@api_view(["POST"])
def IdealWeight(heightdata):
    try:
        height=json.loads(heightdata.body)
        weight=str(height*10)
        return JsonResponse("Ideal weight should be:"+weight+" kg",safe=False)
    except ValueError as e:
        return Response(e.args[0],status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def index(request):
    formData = request.FILES
    # img1 = skio.imread(formData['Image-1'])
    # img2 = skio.imread(formData['Image-2'])
    img1 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/obama_small.jpg')
    img2 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/george_small.jpg')
    morphed_img = morph(img1, img2, 0.5)
    encodedImg = base64.b64encode(img1)
    return Response("Hello")
