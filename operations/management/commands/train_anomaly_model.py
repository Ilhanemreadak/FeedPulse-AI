import os

import joblib
import pandas as pd
from django.core.management.base import BaseCommand

from operations.models import ProductionRecord
from operations.services.anomaly_service import (
    MODEL_PATH,
    SCALER_PATH,
    calculate_risk_level,
    get_feature_columns,
)


class Command(BaseCommand):
    help = 'IsolationForest modelini DB verisi üzerinde eğit'

    def handle(self, *args, **options):
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler

        feature_cols = get_feature_columns()
        qs = ProductionRecord.objects.values('id', *feature_cols)
        df = pd.DataFrame(list(qs))

        if df.empty:
            self.stderr.write("DB'de veri yok. Önce import_dataset çalıştırın.")
            return

        self.stdout.write(f"Eğitim başlıyor: {len(df)} kayıt...")

        ids = df['id'].tolist()
        for col in feature_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(df[col].median())

        X_raw = df[feature_cols].values
        scaler = StandardScaler()
        X = scaler.fit_transform(X_raw)

        model = IsolationForest(n_estimators=200, contamination=0.08, random_state=42)
        model.fit(X)

        predictions = model.predict(X)
        scores = model.decision_function(X)

        os.makedirs(MODEL_PATH.parent, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
        self.stdout.write(f"Model kaydedildi -> {MODEL_PATH}")

        batch = [(ids[i], predictions[i] == -1, float(scores[i])) for i in range(len(ids))]
        pk_map = {pk: (is_anom, score) for pk, is_anom, score in batch}

        records_to_update = []
        for record in ProductionRecord.objects.filter(id__in=ids):
            is_anom, score = pk_map[record.id]
            record.predicted_anomaly = is_anom
            record.anomaly_score = round(score, 4)
            record.risk_level = calculate_risk_level(score)
            records_to_update.append(record)

        ProductionRecord.objects.bulk_update(
            records_to_update, ['predicted_anomaly', 'anomaly_score', 'risk_level'], batch_size=500
        )

        anom_count = sum(1 for _, is_anom, _ in batch if is_anom)
        total = len(batch)
        rate = round(anom_count / total * 100, 1)
        self.stdout.write(
            self.style.SUCCESS(
                f"Eğitim tamamlandı | Toplam: {total} | Anomali: {anom_count} ({rate}%)"
            )
        )
