from rest_framework import fields, serializers
from .models import Testfile

class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testfile
        fields = '__all__'