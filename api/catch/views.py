from enum import auto
import uuid, os, threading, json, socket
from os import name
from _thread import *
from queue import Empty, Queue
from subprocess import run, PIPE
from django.core.files.storage import default_storage
from django.db.models.query import QuerySet
from django.http import response, JsonResponse, FileResponse
from django.http.response import FileResponse, HttpResponse
from django.shortcuts import render, resolve_url
from django.db import transaction
from django.core.files.base import ContentFile

from datetime import datetime

from rest_framework import serializers, viewsets, status
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import api_view, parser_classes, renderer_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser, JSONParser, MultiPartParser
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer

from .models import Test, Upload, Train
from .serializers import TestSerializer, TrainSerializer, UploadSerializer
from django.conf import settings
from catch.tasks import RunUserData

port = 48762
thread_count = 0
# For downloading the combine.py file(model)
@api_view(('GET',))
def downloadModel(request):
    try:
        uid = request.query_params['train_id']
        print(uid)

        if uid != None:
            path = settings.MEDIA_ROOT + f"/{uid}"
            model = open(path + "/combine.py", "rb")
            
            # Setup response content-type
            response = FileResponse(model)
            response['Content-Type']='application/octet-stream'
            response['Content-Disposition']='attachment;filename="' + uid + '.py"'
    except:
        response = Response("NO TRAINING ID!", status=status.HTTP_400_BAD_REQUEST)

    return response

#CNN model
def cnn(f, models):
    f.write("import tensorflow as tf\n"
    +"from tensorflow import keras\n"
    +"from tensorflow.keras import datasets, layers, models\n"
    +"print(\"CNN TRAINING START!\\n\\n\")\n"
    +"(train_images, train_labels), (test_images, test_labels) = datasets.cifar10.load_data()\n"
    +"# Normalize pixel values to be between 0 and 1\n"
    +"train_images, test_images = train_images / 255.0, test_images / 255.0\n"
    +"model = models.Sequential()\n\n")

    f.write("class CustomCallback(keras.callbacks.Callback):\n"
    +"  def on_train_end(self, logs=None):\n"
    +"      print(\"\\n----Training Done!----\")\n\n"
    +"  def on_epoch_end(self, epoch, logs=None):\n"
    +"      print(\"Now epoch count is: {}\".format(epoch))\n\n"
    +"  def on_train_batch_end(self, batch, logs=None):\n"
    +"      print(\"Now batch is: {}\".format(batch))\n\n")

    for model in models:
        if model['id']==1:
            f.write("model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)))\n")
        elif model['id']==2:
            f.write("model.add(layers.MaxPooling2D((2, 2)))\n")
        elif model['id']==3:
            f.write("model.add(layers.Conv2D(64, (3, 3), activation='relu'))\n")
        elif model['id']==4:
            f.write("model.add(layers.Flatten())\n"
            +"model.add(layers.Dense(64, activation='relu'))\n"
            +"model.add(layers.Dense(10))\n")
    
    f.write("model.compile(optimizer='adam',loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),metrics=['accuracy'])\n"
    +"model.summary()\n"
    +"model.fit(train_images, train_labels, epochs=10, callbacks=[CustomCallback()], validation_data=(test_images, test_labels))\n"
    +"#history = model.fit(train_images, train_labels, epochs=10, validation_data=(test_images, test_labels))\n"
    +"#test_loss, test_acc = model.evaluate(test_images,  test_labels, verbose=2)\n"
    +"#print(test_acc)\n")

def cnn2(f, models, uid, port, fn):
    f.write("import tensorflow as tf\n"
    +"import numpy as np\n"
    +"from tensorflow import keras\n"
    +"from tensorflow.keras import layers, models\n"
    +"\nimport socket\n"
    +"ServerSocket = socket.socket()\n"
    +"ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
    +"host = '140.136.151.88'\n"
    +"port = " + str(port) + "\n\n"
    +"try:\n"
    +"    ServerSocket.bind((host, port))\n"
    +"except socket.error as e:\n"
    +"    print(str(e))\n\n"
    +"print('Waiting for a Connection..')\n"
    +"ServerSocket.listen(1)\n"
    +"conn, address = ServerSocket.accept()\n"
    +"print('Connected to: ' + address[0] + ':' + str(address[1]))\n\n")

    f.write("print(\"CNN TRAINING START!\\n\\n\")\n"
    +"uid = '" + str(uid) + "'\n"
    +"file_name = '" + fn + "'\n"
    +"train = np.load('/home/b04/桌面/Github/Api/api/media/'+ uid + '/' + file_name)\n"
    +"train_images, train_labels = train['train_img'], train['train_lab']\n"
    +"test_images, test_labels = train['test_img'], train['test_lab']\n"
    +"train_images = train_images / 255.0\n"
    +"test_images = test_images / 255.0\n\n"
    +"model = models.Sequential()\n\n")
    

    f.write("class CustomCallback(keras.callbacks.Callback):\n"
    +"    global conn\n"
    +"    def on_train_end(self, logs=None):\n"
    +"        keys = list(logs.keys())\n"
    +"        print(\"THE KEY is {}\".format(keys))\n"
    +"        print(logs['accuracy'], logs['val_accuracy'])\n"
    +"        print(\"\\n----Training Done!----\")\n"
    +"        conn.send(str.encode(\"!\"+str(logs['accuracy'])))\n"
    +"        conn.send(str.encode(\"!\"+str(logs['val_accuracy'])))\n"
    +"        conn.send(str.encode(\"Training Done!\"))\n"
    +"        conn.send(str.encode(\"over\"))\n"
    +"        conn.close()\n"
    +"    def on_epoch_end(self, epoch, logs=None):\n"
    +"        conn.send(str.encode(\"#\"+str(epoch+1)))\n"
    +"    def on_train_batch_end(self, batch, logs=None):\n"
    +"        conn.send(str.encode(\"@\"+str(batch+1)))\n\n")

    for model in models:
        if model['id']==1:
            if 'input_shape' not in model:
                f.write("model.add(layers.Conv2D("+model['filters']+", "+model['kernel_size']+", padding='"+model['padding']+"', activation='"+model['activation']+"'))\n")
            else:
                f.write("model.add(layers.Conv2D("+model['filters']+", "+model['kernel_size']+", padding='"+model['padding']+"', activation='"+model['activation']+"', input_shape=("+model['input_shape'][0]+", "+model['input_shape'][1]+", 3)))\n")
        elif model['id']==2:
            f.write("model.add(layers.MaxPooling2D(pool_size="+model['pool_size']+"))\n")
        elif model['id']==3:
            f.write("model.add(layers.Flatten())\n")
        elif model['id']==4:
            f.write("model.add(layers.Dense("+model['units']+", activation='"+model['activation']+"'))\n")
    
    f.write("model.compile(optimizer='adam',loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),metrics=['accuracy'])\n"
    +"model.summary()\n"
    +"model.fit(train_images, train_labels, epochs=1, callbacks=[CustomCallback()], validation_data=(test_images, test_labels))\n"
    +"#history = model.fit(train_images, train_labels, epochs=10, callbacks=[CustomCallback()], validation_data=(test_images, test_labels))\n"
    +"#test_loss, test_acc = model.evaluate(test_images,  test_labels, verbose=2)\n"
    +"#print(test_acc)\n")

def create_thread(path, uid):
    with open(path + "/combine.py", "r") as r:
        exec(r.read())


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

        try:
            uid = request.query_params['train_id']
            print(uid)

            if uid != None:
                # Use filter instead get if that type is uniterable
                status = Train.objects.filter(train_id=uid)
                serializers = TrainSerializer(status, many=True)
        except:
            status = self.get_query()
            serializers = TrainSerializer(status, many=True)

        # print(serializers.data)
        return Response(serializers.data)

    def post(self, request, format=None):
        
        global port
        port += 1
        # To get list of files and code id
        fileUpload = request.FILES.getlist('file')
        print(fileUpload[0].name)
        models = request.data.get('model')

        # modelID = request.data.getlist('model')
        # IDs = list(map(int, modelID))

        # Use json to load string as json object
        modelIN = json.loads(models)
        for i in modelIN:
            id = i['id']
            print("id is", id)
            if id == 1:
                print(i['filters'])
                print(i['kernel_size'])
                print(i['padding'])
                print(i['activation'])
            elif id == 2:
                print(i['pool_size'])
            elif id == 3:
                continue
            else:
                print(i['units'])
                print(i['activation'])

                
        # Create uuid to be path
        userID = uuid.uuid4().hex
        path = settings.MEDIA_ROOT + f"/{userID}"
        os.mkdir(path)

        ans = ""
        for i in fileUpload:
            ans += i.name
            # Store list of files with absolutely path
            default_storage.save(path + "/" + i.name, ContentFile(i.read()))

        f = open(path + "/combine.py", "w+")

        cnn2(f, modelIN, userID, port, fileUpload[0].name)
        f.close()
        
        # Take mission for Celery worker to run file
        RunUserData.delay(path, userID)
        
        # path2 = settings.MEDIA_ROOT
        # start_new_thread(create_thread,(path2,userID,))
        # start_new_thread(create_thread,(path,userID,))
        # global thread_count
        # thread_count += 1
        print('Port Number: ' + str(port))
        print('Thread Number: ' + str(thread_count))

        # Response with files' names and uuid for user
        return Response(ans + " " + str(userID) + " " + str(port))

# Test for GET and POST methods, had implemented by viewsets
class TestViewSet(viewsets.ModelViewSet):
    serializer_class = TestSerializer
    queryset = Test.objects.all()