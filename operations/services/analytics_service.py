"""Dashboard aggregation logic shared by the API summary and the HTML dashboard."""

from django.db.models import Avg, Count
from django.db.models.functions import TruncDate

from operations.models import ProductionRecord

DAILY_TREND_LIMIT = 30


def compute_dashboard_stats() -> dict:
    """Compute anomaly/quality aggregations over all production records.

    Returns raw values (no JSON serialization) so each caller can format as needed.
    When the table is empty, ``total_records`` is 0 and the rest fall back to neutral
    defaults.
    """
    total = ProductionRecord.objects.count()
    anomalies = ProductionRecord.objects.filter(predicted_anomaly=True)
    anomaly_count = anomalies.count()
    anomaly_rate = round(anomaly_count / total * 100, 1) if total else 0

    avg_quality = ProductionRecord.objects.aggregate(v=Avg('production_quality_score'))['v']
    avg_energy = ProductionRecord.objects.aggregate(v=Avg('energy_consumption'))['v']

    factory_anomalies = list(
        anomalies.values('factory').annotate(count=Count('id')).order_by('-count')
    )
    riskiest_factory = factory_anomalies[0]['factory'] if factory_anomalies else 'N/A'

    risk_distribution = list(anomalies.values('risk_level').annotate(count=Count('id')))

    daily_trend = list(
        anomalies.annotate(date=TruncDate('timestamp'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')[:DAILY_TREND_LIMIT]
    )
    daily_anomaly_trend = [{'date': str(d['date']), 'count': d['count']} for d in daily_trend]

    return {
        'total_records': total,
        'anomaly_count': anomaly_count,
        'anomaly_rate': anomaly_rate,
        'average_quality_score': round(avg_quality, 1) if avg_quality else None,
        'average_energy_consumption': round(avg_energy, 2) if avg_energy else None,
        'riskiest_factory': riskiest_factory,
        'factory_anomaly_counts': factory_anomalies,
        'risk_distribution': risk_distribution,
        'daily_anomaly_trend': daily_anomaly_trend,
    }
