from enum import auto
import uuid, os, threading, json
from os import name
from queue import Empty, Queue
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

from .models import Test, Upload, Train
from .serializers import TestSerializer, TrainSerializer, UploadSerializer
from django.conf import settings
from catch.tasks import RunUserData

#CNN model
def cnn(f,id):
    f.write("import tensorflow as tf\n"
    +"from tensorflow.keras import datasets, layers, models\n"
    +"print(\"CNN TRAINING START!\\n\\n\")\n"
    +"(train_images, train_labels), (test_images, test_labels) = datasets.cifar10.load_data()\n"
    +"# Normalize pixel values to be between 0 and 1\n"
    +"train_images, test_images = train_images / 255.0, test_images / 255.0\n"
    +"model = models.Sequential()\n")

    for i in id:
        if i==1:
            f.write("model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)))\n")
        elif i==2:
            f.write("model.add(layers.MaxPooling2D((2, 2)))\n")
        elif i==3:
            f.write("model.add(layers.Conv2D(64, (3, 3), activation='relu'))\n")
        elif i==4:
            f.write("model.add(layers.Flatten())\n"
            +"model.add(layers.Dense(64, activation='relu'))\n"
            +"model.add(layers.Dense(10))\n")
    
    f.write("model.compile(optimizer='adam',loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),metrics=['accuracy'])\n"
    +"model.summary()\n"
    +"model.fit(train_images, train_labels, epochs=10, validation_data=(test_images, test_labels))\n"
    +"#history = model.fit(train_images, train_labels, epochs=10, validation_data=(test_images, test_labels))\n"
    +"#test_loss, test_acc = model.evaluate(test_images,  test_labels, verbose=2)\n"
    +"#print(test_acc)\n")

def cnn2(f,models):
    f.write("import tensorflow as tf\n"
    +"from tensorflow.keras import datasets, layers, models\n"
    +"print(\"CNN TRAINING START!\\n\\n\")\n"
    +"(train_images, train_labels), (test_images, test_labels) = datasets.cifar10.load_data()\n"
    +"# Normalize pixel values to be between 0 and 1\n"
    +"train_images, test_images = train_images / 255.0, test_images / 255.0\n"
    +"model = models.Sequential()\n")

    for model in models:
        if model['id']==1:
            f.write("model.add(layers.Conv2D("+model['filters']+", "+model['kernel_size']+", activation="+model['activation']+"))\n")
        elif model['id']==2:
            f.write("model.add(layers.MaxPooling2D(pool_size="+model['pool_size']+"))\n")
        elif model['id']==3:
            f.write("model.add(layers.Flatten())\n")
        elif model['id']==4:
            f.write("model.add(layers.Dense("+model['units']+", activation="+model['activation']+"))\n")
    
    f.write("model.compile(optimizer='adam',loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),metrics=['accuracy'])\n"
    +"model.summary()\n"
    +"model.fit(train_images, train_labels, epochs=10, validation_data=(test_images, test_labels))\n"
    +"#history = model.fit(train_images, train_labels, epochs=10, validation_data=(test_images, test_labels))\n"
    +"#test_loss, test_acc = model.evaluate(test_images,  test_labels, verbose=2)\n"
    +"#print(test_acc)\n")

# Combine CNN model's with id programs
# def GetUserData(f, id):
#     path = settings.PROJECT_ROOT + "/train/CNN/"

#     with open(path + "base.py", "r") as b:
#         f.write(b.read())

#     for i in id:
#         with open(path + f"{i}.py", "r") as tmp:
#             f.write(tmp.read())
    
#     with open(path + "end.py", "r") as e:
#         f.write(e.read()) 

def catch(request):
    return render(request, 'catch.html', {
        'current_time': str(datetime.now()),
    })

# Test for upload file
class UploadViewSet(APIView):
    # parser_classes = [MultiPartParser]
    serializer_class = TrainSerializer

    # GET for training status
    def get_query(self):
        train_status = Train.objects.all()
        return train_status

    def get(self, request, format=None):
        uid = request.query_params['train_id']
        print(uid)

        if uid != None:
            status = Train.objects.filter(train_id=uid)
            serializers = TrainSerializer(status, many=True)
        else:
            status = self.get_query()
            serializers = TrainSerializer(status, many=True)

        print(serializers.data)
        return Response(serializers.data)

    def post(self, request, format=None):

        # To get list of files and code id
        fileUpload = request.FILES.getlist('file')
        # modelID = request.data.get('model')
        modelID = request.data.getlist('model')
        
        # Use json to load string as json object
        # IDs = json.loads(modelID)
        # for i in IDs:
        #     print(i['id'])

        IDs = list(map(int, modelID))

        # Create uuid to be path
        userID = uuid.uuid4().hex
        path = settings.MEDIA_ROOT + f"/{userID}"
        os.mkdir(path)

        # Store a simple train status
        new_train = Train.objects.create(
            train_id=userID, 
            complete=False, 
            progress_epoch=0,
            start_date=auto)

        print(new_train.start_date)
        new_train.save()

        ans = ""
        for i in fileUpload:
            ans += " " + i.name
            # Store list of files with absolutely path
            default_storage.save(path + "/" + i.name, ContentFile(i.read()))

        f = open(path + "/combine.py", "w+")
        #GetUserData(f, IDs)
        cnn(f,IDs)
        f.close()
        
        # Take mission for Celery worker to run file
        RunUserData.delay(path, userID)
        

        # Response with files' names and uuid for user
        return Response(f"{ans} {userID}")

# Test for GET and POST methods, had implemented by viewsets
class TestViewSet(viewsets.ModelViewSet):
    serializer_class = TestSerializer
    queryset = Test.objects.all()