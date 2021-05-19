from django.http.response import HttpResponse
from django.shortcuts import render, resolve_url
from rest_framework import serializers, viewsets
from django.http import JsonResponse
from django.db import transaction
from rest_framework.generics import GenericAPIView

from datetime import datetime
from .models import Testfile
from .serializers import TestSerializer

# Create your views here.

def catch(request):
    return render(request, 'catch.html', {
        'current_time': str(datetime.now()),
    })

class TestView(viewsets.ModelViewSet):
    quertset = Testfile.objects.all()
    serializer_class = TestSerializer