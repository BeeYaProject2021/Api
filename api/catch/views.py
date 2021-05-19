from django.shortcuts import render, resolve_url
from rest_framework import serializers, viewsets
from django.http import JsonResponse
from django.db import transaction
from rest_framework.generics import GenericAPIView


from .models import Testfile
from .serializers import TestSerializer

# Create your views here.
class TestView(viewsets.ModelViewSet):
    quertset = Testfile.objects.all()
    serializer_class = TestSerializer