from django.contrib import admin

from .models import ProductionRecord


@admin.register(ProductionRecord)
class ProductionRecordAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'factory',
        'line_id',
        'product_type',
        'predicted_anomaly',
        'risk_level',
        'anomaly_score',
    ]
    list_filter = ['factory', 'line_id', 'product_type', 'predicted_anomaly', 'risk_level']
    search_fields = ['factory', 'line_id', 'product_type']
