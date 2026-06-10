from django.db import models


class ProductionRecord(models.Model):
    timestamp = models.DateTimeField()
    factory = models.CharField(max_length=100)
    line_id = models.CharField(max_length=20)
    product_type = models.CharField(max_length=100)
    temperature = models.FloatField(null=True, blank=True)
    machine_speed = models.FloatField(null=True, blank=True)
    vibration_level = models.FloatField(null=True, blank=True)
    energy_consumption = models.FloatField(null=True, blank=True)
    production_quality_score = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    production_volume = models.FloatField(null=True, blank=True)
    optimal_condition = models.BooleanField(null=True, blank=True)
    is_anomaly = models.BooleanField(default=False)
    predicted_anomaly = models.BooleanField(default=False)
    anomaly_score = models.FloatField(null=True, blank=True)
    risk_level = models.CharField(max_length=20, default='low')
    anomaly_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.factory} - {self.line_id} - {self.product_type} - {self.timestamp}"
