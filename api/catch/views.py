from django.http import response, JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import render, resolve_url
from django.db import transaction

from datetime import datetime

from rest_framework import serializers, viewsets, status
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Test
from .serializers import TestSerializer, UploadSerializer

# Create your views here.

def catch(request):
    return render(request, 'catch.html', {
        'current_time': str(datetime.now()),
    })

# Test for upload file
class UploadViewSet(ViewSet):
    serializer_class = UploadSerializer

    @api_view(['GET', 'POST'])
    def UploadList(request):
        if request.method == 'GET':
            return Response("GET API")

        elif request.method == 'POST':
            serializers = UploadSerializer(data=request.data)
            if serializers.is_valid():
                serializers.save()
                return Response(serializers.data, status=status.HTTP_201_CREATED)
            return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)
    # def get(self, request):
    #     return Response("GET API")
    
    # def post(self, request):
    #     fileUpload = request.FILES.get('fileUpload')
    #     content_type = fileUpload.content_type
    #     response = "POST API -> Upload {} file".format(content_type)
    #     return Response(response)

# Test for GET and POST methods
class TestViewSet(APIView):
    serializer_class = TestSerializer

    def getQuery(self):
        testFile = Test.objects.all()
        return testFile
    
    def get(self, request, *args, **kwargs):
        testFile = self.getQuery()
        serializer = TestSerializer(testFile, many=True)

        return Response(serializer.data)
    
    # Give POST blanks and fill up will create new data 
    def post(self, request, *args, **kwargs):
        testData = request.data
        newData = Test.objects.create(
            name = testData['name'],
            text = testData['text']
        )
        newData.save()

        serializer = TestSerializer(newData)
        return Response(serializer.data)
