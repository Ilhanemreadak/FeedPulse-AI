import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from operations.models import ProductionRecord
from operations.services.data_mapping_service import map_columns

FACTORIES = ['Karacabey', 'Konya', 'Tekirdağ', 'Manisa', 'Samsun',
             'Gaziantep', 'Burdur', 'Polatlı', 'Diyarbakır']
LINES = ['L1', 'L2', 'L3', 'L4']
PRODUCT_TYPES = ['Büyükbaş Yemi', 'Küçükbaş Yemi', 'Kanatlı Yemi', 'Özel Yem', 'Kedi Köpek Maması']


def _safe_float(val):
    try:
        if val is None:
            return None
        f = float(val)
        return None if np.isnan(f) else f
    except (TypeError, ValueError):
        return None


class Command(BaseCommand):
    help = 'CSV veri setini ProductionRecord tablosuna import et'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)

    def handle(self, *args, **options):
        path = options['csv_file']
        try:
            df = pd.read_csv(path)
        except FileNotFoundError:
            raise CommandError(f"Dosya bulunamadı: {path}")

        self.stdout.write(f"Yüklendi: {len(df)} satır, {path}")
        self.stdout.write(f"Kolonlar: {list(df.columns)}")

        df = map_columns(df)
        self.stdout.write(f"Eşleşen kolonlar: {list(df.columns)}")

        # --- timestamp ---
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        else:
            base = datetime(2026, 1, 1, 6, 0, 0)
            df['timestamp'] = [base + timedelta(hours=i) for i in range(len(df))]

        # --- synthetic fields if missing ---
        if 'factory' not in df.columns:
            df['factory'] = [random.choice(FACTORIES) for _ in range(len(df))]
        if 'line_id' not in df.columns:
            df['line_id'] = [random.choice(LINES) for _ in range(len(df))]
        if 'product_type' not in df.columns:
            df['product_type'] = [random.choice(PRODUCT_TYPES) for _ in range(len(df))]
        if 'humidity' not in df.columns:
            df['humidity'] = np.random.uniform(40, 80, len(df)).round(2)
        if 'pressure' not in df.columns:
            df['pressure'] = np.random.uniform(2, 7, len(df)).round(2)
        if 'production_volume' not in df.columns:
            df['production_volume'] = np.random.uniform(40, 100, len(df)).round(2)

        # --- quality score normalization: 0-10 scale → 0-100 ---
        if 'production_quality_score' in df.columns:
            df['production_quality_score'] = pd.to_numeric(
                df['production_quality_score'], errors='coerce'
            )
            max_q = df['production_quality_score'].max()
            if max_q is not None and not np.isnan(max_q) and max_q <= 10:
                df['production_quality_score'] = (df['production_quality_score'] * 10).round(2)

        # --- is_anomaly derivation ---
        if 'is_anomaly' not in df.columns:
            if 'optimal_condition' in df.columns:
                df['is_anomaly'] = df['optimal_condition'].apply(
                    lambda x: x == 0 or x is False or str(x) == '0'
                )
            else:
                df['is_anomaly'] = False

        # --- optimal_condition as bool ---
        if 'optimal_condition' in df.columns:
            df['optimal_condition'] = df['optimal_condition'].apply(
                lambda x: x == 1 or x is True or str(x) == '1'
            )

        numeric_cols = [
            'temperature', 'machine_speed', 'vibration_level', 'energy_consumption',
            'production_quality_score', 'humidity', 'pressure', 'production_volume',
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        ProductionRecord.objects.all().delete()
        self.stdout.write("Mevcut kayıtlar silindi.")

        records = []
        for _, row in df.iterrows():
            ts = row.get('timestamp')
            if pd.isnull(ts):
                ts = timezone.now()
            else:
                try:
                    ts = timezone.make_aware(
                        ts.to_pydatetime() if hasattr(ts, 'to_pydatetime') else ts
                    )
                except Exception:
                    ts = timezone.now()

            records.append(ProductionRecord(
                timestamp=ts,
                factory=str(row.get('factory', 'Unknown')),
                line_id=str(row.get('line_id', 'L1')),
                product_type=str(row.get('product_type', 'Bilinmiyor')),
                temperature=_safe_float(row.get('temperature')),
                machine_speed=_safe_float(row.get('machine_speed')),
                vibration_level=_safe_float(row.get('vibration_level')),
                energy_consumption=_safe_float(row.get('energy_consumption')),
                production_quality_score=_safe_float(row.get('production_quality_score')),
                humidity=_safe_float(row.get('humidity')),
                pressure=_safe_float(row.get('pressure')),
                production_volume=_safe_float(row.get('production_volume')),
                optimal_condition=bool(row.get('optimal_condition', True)),
                is_anomaly=bool(row.get('is_anomaly', False)),
                anomaly_reason=str(row.get('anomaly_reason', '') or ''),
            ))

        ProductionRecord.objects.bulk_create(records, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"Import tamamlandı: {len(records)} kayıt eklendi."))
