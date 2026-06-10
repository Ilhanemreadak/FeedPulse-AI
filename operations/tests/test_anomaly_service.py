import pytest

from operations.services import anomaly_service
from operations.services.anomaly_service import (
    calculate_risk_level,
    get_feature_columns,
    predict_single_record,
)


@pytest.mark.parametrize(
    'score, expected',
    [
        (-0.05, 'high'),
        (-0.041, 'high'),
        (-0.04, 'medium'),  # boundary: not < -0.04
        (-0.03, 'medium'),
        (-0.02, 'low'),  # boundary: not < -0.02
        (0.0, 'low'),
        (0.5, 'low'),
    ],
)
def test_calculate_risk_level_thresholds(score, expected):
    assert calculate_risk_level(score) == expected


def test_get_feature_columns_has_eight_features():
    cols = get_feature_columns()
    assert len(cols) == 8
    assert 'temperature' in cols
    assert 'production_volume' in cols


def test_predict_single_record_missing_model_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(anomaly_service, 'MODEL_PATH', tmp_path / 'missing.joblib')
    monkeypatch.setattr(anomaly_service, 'SCALER_PATH', tmp_path / 'missing_scaler.joblib')
    with pytest.raises(FileNotFoundError):
        predict_single_record({'temperature': 90})


def test_predict_single_record_happy_path(monkeypatch):
    class FakeScaler:
        def transform(self, rows):
            return rows

    class FakeModel:
        def predict(self, X):
            return [-1]

        def decision_function(self, X):
            return [-0.05]

    monkeypatch.setattr(
        anomaly_service, 'load_model_and_scaler', lambda: (FakeModel(), FakeScaler())
    )
    result = predict_single_record({'temperature': 95, 'vibration_level': 9})
    assert result['predicted_anomaly'] is True
    assert result['anomaly_score'] == -0.05
    assert result['risk_level'] == 'high'
