import json

from django.db.models import Avg
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from .models import ProductionRecord
from .serializers import ProductionRecordSerializer
from .services.analytics_service import compute_dashboard_stats
from .services.anomaly_service import predict_single_record
from .services.explanation_service import answer_question, generate_explanation

RECENT_RECORDS_LIMIT = 50


def _paginated_records_response(request: Request, queryset) -> Response:
    """Serialize a record queryset through the default page-number paginator."""
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = ProductionRecordSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def api_summary(request: Request) -> Response:
    """Return dashboard aggregations as JSON."""
    stats = compute_dashboard_stats()
    if stats['total_records'] == 0:
        return Response({'error': 'Veri yok. import_dataset komutunu çalıştırın.'})
    return Response(stats)


@api_view(['GET'])
def api_records(request: Request) -> Response:
    """Return a paginated list of all production records."""
    return _paginated_records_response(request, ProductionRecord.objects.all())


@api_view(['GET'])
def api_anomalies(request: Request) -> Response:
    """Return a paginated list of records flagged as anomalies."""
    qs = ProductionRecord.objects.filter(predicted_anomaly=True)
    return _paginated_records_response(request, qs)


@api_view(['GET'])
def api_record_detail(request: Request, pk: int) -> Response:
    """Return the full serialized record for a single primary key."""
    record = get_object_or_404(ProductionRecord, pk=pk)
    serializer = ProductionRecordSerializer(record)
    return Response(serializer.data)


@api_view(['GET'])
def api_explain(request: Request, pk: int) -> Response:
    """Return the anomaly explanation (LLM or rule-based) for a single record."""
    record = get_object_or_404(ProductionRecord, pk=pk)
    explanation = generate_explanation(record.feature_dict())
    return Response(
        {
            'record_id': pk,
            'predicted_anomaly': record.predicted_anomaly,
            'anomaly_score': record.anomaly_score,
            'risk_level': record.risk_level,
            'explanation': explanation,
        }
    )


@api_view(['POST'])
def api_ask(request: Request, pk: int) -> Response:
    """Answer a free-form question about a single record."""
    record = get_object_or_404(ProductionRecord, pk=pk)
    question = (request.data.get('question') or '').strip()
    if not question:
        return Response({'error': 'Soru boş olamaz.'}, status=status.HTTP_400_BAD_REQUEST)
    answer = answer_question(record.context_dict(), question)
    return Response({'question': question, 'answer': answer})


@api_view(['POST'])
def api_predict(request: Request) -> Response:
    """Run a single ad-hoc prediction on posted feature values."""
    try:
        data = request.data
        result = predict_single_record(data)
        result['explanation'] = generate_explanation(data)
        return Response(result)
    except FileNotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Render the HTML dashboard with aggregations and chart payloads."""
    stats = compute_dashboard_stats()

    product_quality = list(
        ProductionRecord.objects.values('product_type')
        .annotate(avg_quality=Avg('production_quality_score'))
        .order_by('product_type')
    )

    context = {
        'total_records': stats['total_records'],
        'anomaly_count': stats['anomaly_count'],
        'anomaly_rate': stats['anomaly_rate'],
        'avg_quality': stats['average_quality_score'] or 0,
        'avg_energy': stats['average_energy_consumption'] or 0,
        'riskiest_factory': stats['riskiest_factory'],
        'factory_anomalies_json': json.dumps(stats['factory_anomaly_counts']),
        'risk_dist_json': json.dumps(stats['risk_distribution']),
        'daily_trend_json': json.dumps(stats['daily_anomaly_trend']),
        'product_quality_json': json.dumps(
            [
                {'product_type': p['product_type'], 'avg_quality': round(p['avg_quality'] or 0, 1)}
                for p in product_quality
            ]
        ),
        'recent_records': ProductionRecord.objects.all()[:RECENT_RECORDS_LIMIT],
    }
    return render(request, 'dashboard.html', context)


def record_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """Render the detail page for a single record with measurements and explanation."""
    record = get_object_or_404(ProductionRecord, pk=pk)
    explanation = generate_explanation(record.feature_dict()) if record.predicted_anomaly else None
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
    return render(
        request,
        'record_detail.html',
        {
            'record': record,
            'explanation': explanation,
            'measurements': measurements,
        },
    )
