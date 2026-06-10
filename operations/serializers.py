from rest_framework import serializers
from .models import ProductionRecord


class ProductionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionRecord
        fields = '__all__'
