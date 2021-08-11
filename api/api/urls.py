"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import include
from django.urls.conf import re_path
from django.views.generic import base

from rest_framework.routers import DefaultRouter
from catch import views
from catch.views import UploadViewSet

router = DefaultRouter()
router.register(r'test', views.TestViewSet)
# router.register(r'train_status', views.TrainViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('catch/', include('catch.urls')),
    path('', include(router.urls)),
    path('upload/', UploadViewSet.as_view()),
    # path('upload/<str:filename>', UploadViewSet.as_view())
]
