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
    try:
        formData = request.FILES
        # img1 = skio.imread(formData['Image-1'])
        # img2 = skio.imread(formData['Image-2'])
        # pdb.set_trace() 
        img1 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/brady.jpg')
        img2 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/manning.jpg')
        morphed_img = morph(img1, img2, 0.5)
        # return Response(morphed_img)
    except Exception as e:
        pdb.set_trace()
        print(e)
        return Response(e)
    else:
        return Response('you got this')
