from .models import Test, Upload
from django.db import models
from rest_framework import fields, serializers
from rest_framework.serializers import Serializer, FileField

class UploadSerializer(Serializer):
    fileUpload = FileField()
    class Meta:
        model = Upload
        fields = '__all__'

class TestSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Test
        fields = (
            'id',
            'name',
            'text'
        )