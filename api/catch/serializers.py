from .models import Test
from django.db import models
from rest_framework import fields, serializers
from rest_framework.serializers import Serializer, FileField

class UploadSerializer(Serializer):
    fileUpload = FileField()
    class Meta:
        fields = ['fileUpload']

class TestSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Test
        fields = (
            'id',
            'name',
            'text'
        )