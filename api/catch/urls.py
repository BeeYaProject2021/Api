from django.urls import path
from . import views


urlpatterns = [
    path('',views.catch,name='catch')
]
