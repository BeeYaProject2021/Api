from django.db import models

# Create your models here.
class Test(models.Model):
    id = models.AutoField(auto_created=True, primary_key=True)
    name = models.CharField(max_length=100)
    text = models.CharField(max_length=100)
    