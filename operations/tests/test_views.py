import pytest
from rest_framework.test import APIClient

from .factories import make_record

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def test_summary_empty_db_returns_error(client):
    resp = client.get('/api/summary/')
    assert resp.status_code == 200
    assert 'error' in resp.data


def test_summary_with_data_returns_stats(client):
    make_record(predicted_anomaly=True, risk_level='high')
    make_record(predicted_anomaly=False)
    resp = client.get('/api/summary/')
    assert resp.data['total_records'] == 2
    assert resp.data['anomaly_count'] == 1
    assert resp.data['anomaly_rate'] == 50.0


def test_records_are_paginated(client):
    for _ in range(3):
        make_record()
    resp = client.get('/api/records/')
    assert resp.status_code == 200
    assert set(resp.data) >= {'count', 'next', 'previous', 'results'}
    assert resp.data['count'] == 3


def test_anomalies_filters_predicted(client):
    make_record(predicted_anomaly=True)
    make_record(predicted_anomaly=False)
    resp = client.get('/api/anomalies/')
    assert resp.data['count'] == 1


def test_record_detail_404_for_missing(client):
    resp = client.get('/api/records/999999/')
    assert resp.status_code == 404


def test_ask_empty_question_returns_400(client):
    record = make_record()
    resp = client.post(f'/api/ask/{record.pk}/', {'question': '  '}, format='json')
    assert resp.status_code == 400
    assert 'error' in resp.data


def test_ask_returns_answer_without_keys(client, monkeypatch):
    for key in [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'DEEPSEEK_API_KEY',
        'GROQ_API_KEY',
        'GEMINI_API_KEY',
    ]:
        monkeypatch.delenv(key, raising=False)
    record = make_record(temperature=95)
    resp = client.post(f'/api/ask/{record.pk}/', {'question': 'Sıcaklık nedir?'}, format='json')
    assert resp.status_code == 200
    assert 'answer' in resp.data
