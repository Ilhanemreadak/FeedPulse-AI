import pytest

from .factories import make_record

pytestmark = pytest.mark.django_db


def test_feature_dict_has_expected_keys():
    record = make_record()
    fd = record.feature_dict()
    assert set(fd) == {
        'temperature',
        'machine_speed',
        'vibration_level',
        'energy_consumption',
        'production_quality_score',
        'humidity',
        'pressure',
        'production_volume',
        'anomaly_score',
    }


def test_context_dict_extends_feature_dict():
    record = make_record(factory='Manisa', risk_level='high')
    cd = record.context_dict()
    assert cd['factory'] == 'Manisa'
    assert cd['risk_level'] == 'high'
    assert cd['line_id'] == record.line_id
    # all feature keys still present
    assert 'temperature' in cd and 'anomaly_score' in cd


def test_str_contains_identity():
    record = make_record(factory='Samsun')
    assert 'Samsun' in str(record)
