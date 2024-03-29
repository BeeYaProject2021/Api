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

from django.utils.functional import empty

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
from catch.tasks import RunUserData, RunTest

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
            zipObj.write(path + "/saved_model.pb", basename(path + "/saved_model.h5"))
            zipObj.close()

            model = open(path + f"/{uid}.zip", "rb")
            # Setup response content-type
            response = FileResponse(model)
            response['Content-Type']='application/zip'
            response['Content-Disposition']='attachment;filename="' + uid + '.zip"'
    except:
        response = Response("NO TRAINING ID!", status=status.HTTP_400_BAD_REQUEST)

    return response

# CNN model
def cnn2(f, path, models, uid, port, fn):
    f.write("import tensorflow as tf\n"
    +"import numpy as np\n"
    +"from tensorflow import keras\n"
    +"from tensorflow.keras import layers, models, optimizers\n"
    +"\nimport socket, time\n"
    +"ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
    +"ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_OOBINLINE, 1)\n"
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

    f.write("gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=0.30)\n"
    +"sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(gpu_options=gpu_options))\n\n"
    +"dataset = " + str(models[0]['dataset']) + "\n")

    if models[0]['dataset'] == 0:
        f.write("print(\"CNN TRAINING START!\\n\\n\")\n"
        +"uid = '" + str(uid) + "'\n"
        +"file_name = '" + fn + "'\n"
        +"train = np.load('"+ path +"' + '/' + file_name)\n"
        +"trainX, trainY = train['train_img'], train['train_lab']\n"
        +"testX, testY = train['test_img'], train['test_lab']\n"
        +"trainX = trainX / 255.0\n"
        +"testX = testX / 255.0\n\n"
        +"model = models.Sequential()\n\n"
        +"img_h = trainX.shape[1]\n"
        +"img_w = trainX.shape[2]\n"
        +"rgb = trainX.shape[3]\n"
        +"input_shape = (img_h, img_w, rgb)\n\n")
    elif models[0]['dataset'] == 1:
        # Else use default
        # mnist(1), fashion_mnist(2), cifar10(3)
        f.write("print(\"CNN TRAINING START!\\n\\n\")\n"
        +"uid = '" + str(uid) + "'\n"
        +"(trainX, trainY), (testX, testY) = keras.datasets.mnist.load_data()\n"
        +"trainX = trainX.reshape(trainX.shape[0], trainX.shape[1], trainX.shape[2], 1)\n"
        +"trainX = trainX / 255.0\n"
        +"testX = testX.reshape(testX.shape[0], testX.shape[1], testX.shape[2], 1)\n"
        +"testX = testX / 255.0\n"
        +"model = models.Sequential()\n\n"
        +"input_shape=(trainX.shape[1], trainX.shape[2], 1)\n\n")
    elif models[0]['dataset'] == 2:
        f.write("print(\"CNN TRAINING START!\\n\\n\")\n"
        +"uid = '" + str(uid) + "'\n"
        +"(trainX, trainY), (testX, testY) = keras.datasets.fashion_mnist.load_data()\n"
        +"trainX = trainX.reshape(trainX.shape[0], trainX.shape[1], trainX.shape[2], 1)\n"
        +"trainX = trainX / 255.0\n"
        +"testX = testX.reshape(testX.shape[0], testX.shape[1], testX.shape[2], 1)\n"
        +"testX = testX / 255.0\n"
        +"model = models.Sequential()\n\n"
        +"input_shape=(trainX.shape[1], trainX.shape[2], 1)\n\n")        
    else:
        f.write("print(\"CNN TRAINING START!\\n\\n\")\n"
        +"uid = '" + str(uid) + "'\n"
        +"(trainX, trainY), (testX, testY) = keras.datasets.cifar10.load_data()\n"
        +"trainX = trainX / 255.0\n"
        +"testX = testX / 255.0\n"
        +"model = models.Sequential()\n\n"
        +"input_shape=(trainX.shape[1], trainX.shape[2], 3)\n\n")   

    # if models[-1]['loss_fn'] != "sparse_categorical_crossentropy":   
    f.write("trainY = keras.utils.to_categorical(trainY)\n"
    +"testY = keras.utils.to_categorical(testY)\n")

    f.write("conn.send(str.encode(str(trainX.shape[0])+\"\\r\\n\"))\n\n")
    
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
    +"        time.sleep(0.03)\n"    
    +"        conn.send(str.encode(f'@{batch+1:02d}@{logs[\"accuracy\"]:015.10f}@{logs[\"loss\"]:015.10f}\\r\\n'))\n\n")

    f.write("try:\n\n")

    f.write("    model.add(layers.InputLayer(input_shape=(input_shape)))\n")
    for model in models:
        if model['id']==1:
            f.write("    model.add(layers.Conv2D("+model['filters']+", "+model['kernel_size']+", strides="+model['strides']+", padding='"+model['padding']+"', activation='"+model['activation']+"'))\n")
        elif model['id']==2:
            f.write("    model.add(layers."+model['pool_type']+"Pooling2D(pool_size="+model['pool_size']+", strides="+model['strides']+"))\n")
        elif model['id']==3:
            f.write("    model.add(layers.Flatten())\n")
        elif model['id']==4:
            f.write("    model.add(layers.Dense("+model['units']+", activation='"+model['activation']+"'))\n")
        elif model['id']==-1:
            f.write("    opt=optimizers."+model['optimizer']+"(lr="+model['learning_rate']+")\n")
            f.write("    model.compile(optimizer=opt,loss='"+model['loss_fn']+"',metrics=['accuracy'])\n"
            +"    model.summary()\n"
            +"    model.fit(trainX, trainY, batch_size="+model['batch_size']+", epochs="+model['epochs']+", callbacks=[CustomCallback()], validation_data=(testX, testY))\n")
    
    f.write("    model.save('"+ path +"' + '/saved_model.h5')\n")
    f.write("except Exception as e:\n"
    +"    conn.send(str.encode(\"error:\" + str(e)))\n"
    +"    print(\"OHNO! \" + str(e))\n"
    +"    conn.close()")

def test_model(f, port, path, batch, img_h, img_w, img_c, fn):
    f.write("import tensorflow as tf\n"
    +"import numpy as np\n"
    +"from tensorflow import keras\n"
    +"from tensorflow.keras import models\n\n")

    f.write("import socket\n"
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

    f.write("test_model = models.load_model('"+ path +"' + '/saved_model.h5')\n"
    +"test_model.summary()\n\n")

    f.write("try:\n")

    if batch != None:
        f.write("    test = np.load('"+ path +"' + '/test.npz')\n")
        f.write("    testX, testY = test['test_img'], test['test_lab']\n"
        +"    testX = testX / 255.0\n"
        +"    testY = keras.utils.to_categorical(testY)\n\n")

        f.write("    result_loss, result_acc = test_model.evaluate(testX, testY, batch_size="+ batch +")\n"
        +"    conn.send(str.encode(f'#{result_loss:015.5f}#{result_acc:015.5f}\\r\\n'))\n"
        +"    print(result_loss, result_acc)\n"
        +"    predicts = test_model.predict(testX)\n"
        +"    possible = np.argmax(predicts, axis=1)\n"
        +"    print(\"size: \", len(possible))\n"
        +"    true = np.argmax(testY, axis=1)\n"
        +"    for i in possible:\n"
        +"        conn.send(str.encode(str(i) + \"\\r\\n\"))\n"
        +"    conn.send(str.encode(\"over\\r\\n\"))\n"
        +"    conn.close()\n")
    else:
        f.write("    filename = '" + fn + "'\n")
        if int(img_c) == 0:
            f.write("    img = tf.keras.preprocessing.image.load_img('"+ path +"' + '/' + filename, target_size=(" +img_h+", " +img_w+"), color_mode=\"grayscale\")\n")
        else:
            f.write("    img = tf.keras.preprocessing.image.load_img('"+ path +"' + '/' + filename, target_size=(" +img_h+", " +img_w+"))\n")
        f.write("    img_arr = tf.keras.preprocessing.image.img_to_array(img)\n"
        +"    img_arr = tf.expand_dims(img_arr, 0)\n"
        +"    predict_img = test_model.predict(img_arr/255.0)\n"
        +"    guess = np.argmax(predict_img[0])\n"
        +"    conn.send(str.encode(f'#{guess}#{np.max(predict_img[0]):.3f}\\r\\n'))\n"
        +"    print(predict_img)\n"
        # +"    conn.send(str.encode(\"over\\r\\n\"))\n"
        +"    conn.close()\n")

    f.write("except Exception as e:\n"
    +"    conn.send(str.encode(\"error:\" + str(e)))\n"
    +"    print(\"OHNO! \" + str(e))\n"
    +"    conn.close()")


def create_thread(path, uid):
    with open(path + "/combine.py", "r") as r:
        exec(r.read())


def catch(request):
    return render(request, 'catch.html', {
        'current_time': str(datetime.now()),
    })

# Upload file and Training
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
        
        file_name = None
        if fileUpload:
            file_name = fileUpload[0].name

        models = request.data.get('model')
        print(models)
        # Use json to load string as json object
        modelIN = json.loads(models)
        # print(modelIN[0]['dataset'])

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

        cnn2(f, path, modelIN, userID, now_port, file_name)
        f.close()
        
        # Take mission for Celery worker to run file
        RunUserData.delay(path, userID)
        print('Port Number: ' + str(now_port))

        # Response with files' names and uuid for user
        return Response(ans + " " + str(userID) + " " + str(now_port))

# Test model
class TestViewSet(APIView):

    def post(self, request, format=None):
        
        global port
        port += 1
        now_port = port
        print('Port Number: ' + str(now_port))
        # To get test file
        fileUpload = request.FILES.getlist('file')
        print(fileUpload[0].name)
        fn = fileUpload[0].name

        uid = request.data.get('uid')
        print(uid)
        batch = request.data.get('batch')
        # print(batch)
        img_h = request.data.get('img_h')
        img_w = request.data.get('img_w')
        img_c = request.data.get('img_c')
        batch_size, h, w, c = None, None, None, None
        if batch:
            batch_size = batch
            print("batch: ", batch_size)
        if img_h:
            h = img_h
        if img_w:
            w = img_w
        if img_c:
            c = img_c
            print("img is: ", c)

        path = settings.MEDIA_ROOT + f"/{uid}"

        if fileUpload[0].name.endswith('.npz'):
            ans = "test.npz"
            for i in fileUpload:
                # Store list of files with absolutely path
                default_storage.save(path + "/" + ans, ContentFile(i.read()))
        else:
            for i in fileUpload:
                default_storage.save(path + "/" + i.name, ContentFile(i.read()))

        f = open(path + "/test.py", "w+")
        test_model(f, now_port, path, batch_size, h, w, c, fn)
        f.close()

        RunTest.delay(path)
        return Response(str(uid) + " " + str(now_port))