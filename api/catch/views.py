import uuid, os, threading, json, socket, zipfile
from os.path import basename
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
from zipfile import ZipFile

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

# For downloading the zip file(model)
@api_view(('GET',))
def downloadModel(request):
    try:
        uid = request.query_params['train_id']
        print(uid)

        if uid != None:
            path = settings.MEDIA_ROOT + f"/{uid}"
            zip_filename = path + f"/{uid}.zip"
            zipObj = zipfile.ZipFile(zip_filename, "w")
            zipObj.write(path + "/combine.py", basename(path + "/combine.py"))
            zipObj.write(path + "/saved_model.pb", basename(path + "/saved_model.pb"))
            zipObj.close()

            model = open(path + f"/{uid}.zip", "rb")
            # Setup response content-type
            response = FileResponse(model)
            response['Content-Type']='application/zip'
            response['Content-Disposition']='attachment;filename="' + uid + '.zip"'
    except:
        response = Response("NO TRAINING ID!", status=status.HTTP_400_BAD_REQUEST)

    return response

#CNN model
def cnn2(f, path, models, uid, port, fn):
    f.write("import tensorflow as tf\n"
    +"import numpy as np\n"
    +"from tensorflow import keras\n"
    +"from tensorflow.keras import layers, models, optimizers\n"
    +"\nimport socket, time\n"
    +"ServerSocket = socket.socket()\n"
    +"ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
    +"host = '140.136.204.132'\n"
    # +"host = '140.136.151.88'\n"
    +"port = " + str(port) + "\n\n"
    +"try:\n"
    +"    ServerSocket.bind((host, port))\n"
    +"except socket.error as e:\n"
    +"    print(str(e))\n\n"
    +"print('Waiting for a Connection..')\n"
    +"ServerSocket.listen(1)\n"
    +"conn, address = ServerSocket.accept()\n"
    +"print('Connected to: ' + address[0] + ':' + str(address[1]))\n\n")

    f.write("gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=0.25)\n"
    +"sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(gpu_options=gpu_options))\n")

    f.write("print(\"CNN TRAINING START!\\n\\n\")\n"
    +"uid = '" + str(uid) + "'\n"
    +"file_name = '" + fn + "'\n"
    +"train = np.load('"+ path +"' + '/' + file_name)\n"
    +"train_images, train_labels = train['train_img'], train['train_lab']\n"
    +"test_images, test_labels = train['test_img'], train['test_lab']\n"
    +"train_images = train_images / 255.0\n"
    +"test_images = test_images / 255.0\n\n"
    +"model = models.Sequential()\n\n")
    
    f.write("class CustomCallback(keras.callbacks.Callback):\n"
    +"    global conn\n"
    +"    def on_train_end(self, logs=None):\n"
    +"        print(\"\\n----Training Done!----\")\n"
    +"        conn.send(str.encode(\"over\\r\\n\"))\n"
    +"        conn.close()\n"
    +"    def on_epoch_end(self, epoch, logs=None):\n"
    +"        time.sleep(0.02)\n"
    +"        conn.send(str.encode(f'#{epoch+1:02d}#{logs[\"accuracy\"]:015.10f}#{logs[\"val_accuracy\"]:015.10f}#{logs[\"loss\"]:015.10f}#{logs[\"val_loss\"]:015.10f}\\r\\n'))\n"
    +"    def on_train_batch_end(self, batch, logs=None):\n"
    +"        time.sleep(0.02)\n"    
    +"        conn.send(str.encode(f'@{batch+1:02d}@{logs[\"accuracy\"]:015.10f}@{logs[\"loss\"]:015.10f}\\r\\n'))\n\n")

    for model in models:
        if model['id']==1:
            # if 'input_shape' not in model:
            f.write("model.add(layers.Conv2D("+model['filters']+", "+model['kernel_size']+", padding='"+model['padding']+"', activation='"+model['activation']+"'))\n")
            # else:
            #     f.write("model.add(layers.Conv2D("+model['filters']+", "+model['kernel_size']+", padding='"+model['padding']+"', activation='"+model['activation']+"', input_shape=("+model['input_shape'][0]+", "+model['input_shape'][1]+", 3)))\n")
        elif model['id']==2:
            f.write("model.add(layers.MaxPooling2D(pool_size="+model['pool_size']+"))\n")
        elif model['id']==3:
            f.write("model.add(layers.Flatten())\n")
        elif model['id']==4:
            f.write("model.add(layers.Dense("+model['units']+", activation='"+model['activation']+"'))\n")
        elif model['id']==5:
            f.write("model.add(layers.Input(shape=("+model['input_shape'][0]+", "+model['input_shape'][1]+", "+model['input_shape'][2]+")))\n")
        elif model['id']==-1:
            f.write("opt=optimizers."+model['optimizer']+"(lr="+model['learning_rate']+")\n")
            f.write("model.compile(optimizer=opt,loss='"+model['loss_fn']+"',metrics=['accuracy'])\n"
            +"model.summary()\n"
            +"model.fit(train_images, train_labels, batch_size="+model['batch_size']+", epochs="+model['epochs']+", callbacks=[CustomCallback()], validation_data=(test_images, test_labels))\n")
    
    f.write("model.save('"+ path +"' + '/')\n")

def create_thread(path, uid):
    with open(path + "/combine.py", "r") as r:
        exec(r.read())


def catch(request):
    return render(request, 'catch.html', {
        'current_time': str(datetime.now()),
    })

# Test for upload file
class UploadViewSet(APIView):
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
        now_port = port
        # To get list of files and code id
        fileUpload = request.FILES.getlist('file')
        print(fileUpload[0].name)
        models = request.data.get('model')
        print(models)
        # Use json to load string as json object
        modelIN = json.loads(models)

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

        cnn2(f, path, modelIN, userID, now_port, fileUpload[0].name)
        f.close()
        
        # Take mission for Celery worker to run file
        RunUserData.delay(path, userID)
        print('Port Number: ' + str(now_port))

        # Response with files' names and uuid for user
        return Response(ans + " " + str(userID) + " " + str(now_port))

# Test for GET and POST methods, had implemented by viewsets
class TestViewSet(viewsets.ModelViewSet):
    serializer_class = TestSerializer
    queryset = Test.objects.all()