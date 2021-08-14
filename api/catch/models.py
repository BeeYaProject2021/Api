import datetime
from os import terminal_size
from django.db import models

# Create your models here.
class Test(models.Model):
    train_id = models.CharField(max_length=100)
    complete = models.BooleanField(null=True)
    progress_epoch = models.IntegerField(null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
class Upload(models.Model):
    files = models.FileField(null=True, upload_to='media')

class Train(models.Model):
    train_id = models.CharField(max_length=100)
    # file_name = models.CharField(max_length=100)
    complete = models.BooleanField(null=True)
    progress_epoch = models.IntegerField(null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)