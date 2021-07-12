import uuid, os, threading
from os import name
from subprocess import run, PIPE
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
from django.conf import settings
from catch.tasks import RunUserData, add

# Combine CNN model's with id programs
def GetUserData(f, id):
    path = settings.PROJECT_ROOT + "/train/TestModel/"

    with open(path + "base.py", "r") as b:
        f.write(b.read())

    for i in id:
        with open(path + f"{i}.py", "r") as tmp:
            f.write(tmp.read())
    
    with open(path + "end.py", "r") as e:
        f.write(e.read())

# def RunUserData(path):
#     # with open(path + "/combine.py", "r") as r:
#     #     exec(r.read())

#     os.system(f"python3 {path}/combine.py") 

def catch(request):
    return render(request, 'catch.html', {
        'current_time': str(datetime.now()),
    })

# Test for upload file
class UploadViewSet(APIView):
    # parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        # To get list of files and code id
        fileUpload = request.FILES.getlist('file')
        modelID = request.data.getlist('model')

        # lock = threading.Lock()

        IDs = list(map(int, modelID))
        # for i in modelID:
        #     IDs.append(int(i))
        
        print(IDs)

        # lock.acquire()

        # Create uuid to be path
        userID = uuid.uuid4().hex
        path = settings.MEDIA_ROOT + f"/{userID}"
        os.mkdir(path)

        ans = ""
        for i in fileUpload:
            ans += " " + i.name
            # Store list of files with absolutely path
            default_storage.save(path + "/" + i.name, ContentFile(i.read()))

        f = open(path + "/combine.py", "w+")
        GetUserData(f, IDs)
        f.close()
        
        # Take mission for Celery worker to run file
        RunUserData.delay(path)
        # lock.release()
        # Call run file to train, choose one to run
        # May be ⚠ DANGER ⚠

            # with open(path + "/combine.py", "r") as r:
            #     exec(r.read())

            # os.system(f"python3 {path}/combine.py")

        # Response with files' names and uuid for user
        return Response(f"{ans} {userID}")

# Test for GET and POST methods, had implemented by viewsets
class TestViewSet(viewsets.ModelViewSet):
    serializer_class = TestSerializer
    queryset = Test.objects.all()
