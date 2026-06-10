import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import ProductionRecord
from .serializers import ProductionRecordSerializer


@api_view(['GET'])
def api_summary(request):
    total = ProductionRecord.objects.count()
    if total == 0:
        return Response({'error': 'Veri yok. import_dataset komutunu çalıştırın.'})

    anomaly_count = ProductionRecord.objects.filter(predicted_anomaly=True).count()
    anomaly_rate = round(anomaly_count / total * 100, 1) if total else 0

    avg_quality = ProductionRecord.objects.aggregate(v=Avg('production_quality_score'))['v']
    avg_energy = ProductionRecord.objects.aggregate(v=Avg('energy_consumption'))['v']

    factory_anomalies = list(
        ProductionRecord.objects.filter(predicted_anomaly=True)
        .values('factory').annotate(count=Count('id')).order_by('-count')
    )
    riskiest = factory_anomalies[0]['factory'] if factory_anomalies else 'N/A'

    risk_dist = list(
        ProductionRecord.objects.filter(predicted_anomaly=True)
        .values('risk_level').annotate(count=Count('id'))
    )

    daily_trend = list(
        ProductionRecord.objects.filter(predicted_anomaly=True)
        .annotate(date=TruncDate('timestamp'))
        .values('date').annotate(count=Count('id'))
        .order_by('date')[:30]
    )

    return Response({
        'total_records': total,
        'anomaly_count': anomaly_count,
        'anomaly_rate': anomaly_rate,
        'average_quality_score': round(avg_quality, 1) if avg_quality else None,
        'average_energy_consumption': round(avg_energy, 2) if avg_energy else None,
        'riskiest_factory': riskiest,
        'factory_anomaly_counts': factory_anomalies,
        'risk_distribution': risk_dist,
        'daily_anomaly_trend': [
            {'date': str(d['date']), 'count': d['count']} for d in daily_trend
        ],
    })


@api_view(['GET'])
def api_records(request):
    qs = ProductionRecord.objects.all()[:100]
    serializer = ProductionRecordSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def api_anomalies(request):
    qs = ProductionRecord.objects.filter(predicted_anomaly=True)[:100]
    serializer = ProductionRecordSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def api_record_detail(request, pk):
    record = get_object_or_404(ProductionRecord, pk=pk)
    serializer = ProductionRecordSerializer(record)
    return Response(serializer.data)


@api_view(['GET'])
def api_explain(request, pk):
    from .services.explanation_service import generate_explanation
    record = get_object_or_404(ProductionRecord, pk=pk)
    data = {
        'temperature': record.temperature,
        'machine_speed': record.machine_speed,
        'vibration_level': record.vibration_level,
        'energy_consumption': record.energy_consumption,
        'production_quality_score': record.production_quality_score,
        'humidity': record.humidity,
        'pressure': record.pressure,
        'production_volume': record.production_volume,
        'anomaly_score': record.anomaly_score,
    }
    explanation = generate_explanation(data)
    return Response({
        'record_id': pk,
        'predicted_anomaly': record.predicted_anomaly,
        'anomaly_score': record.anomaly_score,
        'risk_level': record.risk_level,
        'explanation': explanation,
    })


@api_view(['POST'])
def api_predict(request):
    from .services.anomaly_service import predict_single_record
    from .services.explanation_service import generate_explanation
    try:
        data = request.data
        result = predict_single_record(data)
        explanation = generate_explanation(data)
        result['explanation'] = explanation
        return Response(result)
    except FileNotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


def dashboard_view(request):
    total = ProductionRecord.objects.count()
    anomaly_count = ProductionRecord.objects.filter(predicted_anomaly=True).count()
    anomaly_rate = round(anomaly_count / total * 100, 1) if total else 0
    avg_quality = ProductionRecord.objects.aggregate(v=Avg('production_quality_score'))['v']
    avg_energy = ProductionRecord.objects.aggregate(v=Avg('energy_consumption'))['v']

    factory_anomalies = list(
        ProductionRecord.objects.filter(predicted_anomaly=True)
        .values('factory').annotate(count=Count('id')).order_by('-count')
    )
    riskiest = factory_anomalies[0]['factory'] if factory_anomalies else 'N/A'

    risk_dist = list(
        ProductionRecord.objects.filter(predicted_anomaly=True)
        .values('risk_level').annotate(count=Count('id'))
    )

    daily_trend = list(
        ProductionRecord.objects.filter(predicted_anomaly=True)
        .annotate(date=TruncDate('timestamp'))
        .values('date').annotate(count=Count('id'))
        .order_by('date')[:30]
    )
    daily_trend_json = [{'date': str(d['date']), 'count': d['count']} for d in daily_trend]

    product_quality = list(
        ProductionRecord.objects.values('product_type')
        .annotate(avg_quality=Avg('production_quality_score'))
        .order_by('product_type')
    )

    recent_records = ProductionRecord.objects.all()[:50]

    context = {
        'total_records': total,
        'anomaly_count': anomaly_count,
        'anomaly_rate': anomaly_rate,
        'avg_quality': round(avg_quality, 1) if avg_quality else 0,
        'avg_energy': round(avg_energy, 2) if avg_energy else 0,
        'riskiest_factory': riskiest,
        'factory_anomalies_json': json.dumps(factory_anomalies),
        'risk_dist_json': json.dumps(risk_dist),
        'daily_trend_json': json.dumps(daily_trend_json),
        'product_quality_json': json.dumps([
            {'product_type': p['product_type'],
             'avg_quality': round(p['avg_quality'] or 0, 1)}
            for p in product_quality
        ]),
        'recent_records': recent_records,
    }
    return render(request, 'dashboard.html', context)


def record_detail_view(request, pk):
    from .services.explanation_service import generate_explanation
    record = get_object_or_404(ProductionRecord, pk=pk)
    data = {
        'temperature': record.temperature,
        'machine_speed': record.machine_speed,
        'vibration_level': record.vibration_level,
        'energy_consumption': record.energy_consumption,
        'production_quality_score': record.production_quality_score,
        'humidity': record.humidity,
        'pressure': record.pressure,
        'production_volume': record.production_volume,
        'anomaly_score': record.anomaly_score,
    }
    explanation = generate_explanation(data) if record.predicted_anomaly else None
    measurements = [
        ('Sıcaklık', record.temperature, '°C'),
        ('Makine Hızı', record.machine_speed, 'RPM'),
        ('Titreşim', record.vibration_level, 'mm/s'),
        ('Enerji', record.energy_consumption, 'kWh'),
        ('Kalite Skoru', record.production_quality_score, '/100'),
        ('Nem', record.humidity, '%'),
        ('Basınç', record.pressure, 'bar'),
        ('Üretim Hacmi', record.production_volume, 'unit'),
    ]
    return render(request, 'record_detail.html', {
        'record': record,
        'explanation': explanation,
        'measurements': measurements,
    })
