import os
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / 'ml_models' / 'anomaly_model.joblib'
SCALER_PATH = BASE_DIR / 'ml_models' / 'scaler.joblib'

FEATURE_COLUMNS = [
    'temperature', 'machine_speed', 'vibration_level', 'energy_consumption',
    'production_quality_score', 'humidity', 'pressure', 'production_volume',
]


def get_feature_columns():
    return FEATURE_COLUMNS


def calculate_risk_level(score):
    if score < -0.04:
        return 'high'
    elif score < -0.02:
        return 'medium'
    return 'low'


def load_model_and_scaler():
    if not MODEL_PATH.exists() or not SCALER_PATH.exists():
        raise FileNotFoundError(
            "Model bulunamadı. Çalıştırın: python manage.py train_anomaly_model"
        )
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return model, scaler


def predict_single_record(input_data: dict) -> dict:
    model, scaler = load_model_and_scaler()
    row = [input_data.get(col, 0) or 0 for col in FEATURE_COLUMNS]
    X = scaler.transform([row])
    prediction = model.predict(X)[0]
    score = float(model.decision_function(X)[0])
    return {
        'predicted_anomaly': bool(prediction == -1),
        'anomaly_score': round(score, 4),
        'risk_level': calculate_risk_level(score),
    }
