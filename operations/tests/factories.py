"""Minimal test helpers for building ProductionRecord instances."""

from django.utils import timezone

from operations.models import ProductionRecord

_DEFAULTS = {
    'factory': 'Konya',
    'line_id': 'L1',
    'product_type': 'Büyükbaş Yemi',
    'temperature': 70.0,
    'machine_speed': 1200.0,
    'vibration_level': 3.0,
    'energy_consumption': 50.0,
    'production_quality_score': 92.0,
    'humidity': 55.0,
    'pressure': 3.0,
    'production_volume': 80.0,
    'anomaly_score': 0.05,
    'risk_level': 'low',
}


def make_record(**overrides) -> ProductionRecord:
    """Create and persist a ProductionRecord with sensible defaults."""
    fields = {**_DEFAULTS, 'timestamp': timezone.now(), **overrides}
    return ProductionRecord.objects.create(**fields)
