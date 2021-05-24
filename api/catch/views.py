import uuid
from os import name
from django.core.files.storage import default_storage
from django.db.models.query import QuerySet
from django.http import response, JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import render, resolve_url
from django.db import transaction
from django.core.files.base import ContentFile

from datetime import datetime

from rest_framework import serializers, viewsets, status
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser, JSONParser, MultiPartParser

from .models import Test, Upload
from .serializers import TestSerializer, UploadSerializer


# Create your views here.

def catch(request):
    return render(request, 'catch.html', {
        'current_time': str(datetime.now()),
    })

# Test for upload file
class UploadViewSet(APIView):
    # parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        # To get list of files
        fileUpload = request.FILES.getlist('file')

        ans = ""
        for i in fileUpload:
            ans += " " + i.name
            # Store list of files
            default_storage.save(i.name, ContentFile(i.read()))

        # Response with files' names and uuid for user
        return Response(f"{ans} {uuid.uuid4().hex}")

# Test for GET and POST methods, had implemented by viewsets
class TestViewSet(viewsets.ModelViewSet):
    serializer_class = TestSerializer
    queryset = Test.objects.all()
