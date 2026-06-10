import csv
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand

FACTORIES = ['Karacabey', 'Konya', 'Tekirdağ', 'Manisa', 'Samsun',
             'Gaziantep', 'Burdur', 'Polatlı', 'Diyarbakır']
LINES = ['L1', 'L2', 'L3', 'L4']
PRODUCT_TYPES = ['Büyükbaş Yemi', 'Küçükbaş Yemi', 'Kanatlı Yemi', 'Özel Yem', 'Kedi Köpek Maması']

ANOMALY_SCENARIOS = {
    'HIGH_TEMPERATURE': {
        'temperature': (86, 100), 'energy_consumption': (66, 90),
        'production_quality_score': (50, 75), 'machine_speed': (900, 1200),
        'vibration_level': (1, 4), 'humidity': (40, 60),
        'pressure': (2, 4), 'production_volume': (50, 75),
    },
    'MACHINE_STRESS': {
        'temperature': (80, 95), 'vibration_level': (7.5, 12),
        'machine_speed': (700, 1000), 'energy_consumption': (50, 75),
        'production_quality_score': (60, 80), 'humidity': (40, 60),
        'pressure': (3, 5), 'production_volume': (45, 70),
    },
    'ENERGY_SPIKE': {
        'energy_consumption': (75, 100), 'production_volume': (40, 65),
        'temperature': (60, 80), 'machine_speed': (1000, 1400),
        'vibration_level': (1, 5), 'humidity': (40, 65),
        'pressure': (2, 4), 'production_quality_score': (70, 90),
    },
    'QUALITY_DROP': {
        'production_quality_score': (30, 70), 'temperature': (60, 80),
        'machine_speed': (900, 1300), 'vibration_level': (1, 5),
        'energy_consumption': (35, 55), 'humidity': (40, 65),
        'pressure': (2, 4), 'production_volume': (50, 85),
    },
    'HUMIDITY_PRESSURE_ISSUE': {
        'humidity': (72, 90), 'pressure': (5.5, 7),
        'temperature': (60, 80), 'machine_speed': (1000, 1400),
        'vibration_level': (1, 5), 'energy_consumption': (35, 60),
        'production_quality_score': (65, 85), 'production_volume': (50, 85),
    },
    'PRODUCTION_DROP': {
        'production_volume': (20, 45), 'energy_consumption': (55, 80),
        'temperature': (65, 85), 'machine_speed': (800, 1100),
        'vibration_level': (1, 6), 'humidity': (40, 65),
        'pressure': (2, 5), 'production_quality_score': (60, 85),
    },
}

NORMAL_RANGES = {
    'temperature': (55, 80), 'machine_speed': (1200, 1600),
    'vibration_level': (0.01, 3.5), 'energy_consumption': (1, 55),
    'production_quality_score': (85, 100), 'humidity': (40, 65),
    'pressure': (2, 4.5), 'production_volume': (65, 100),
}


def _rand(low, high):
    return round(random.uniform(low, high), 2)


class Command(BaseCommand):
    help = 'Sentetik FeedPulse veri seti oluştur'

    def add_arguments(self, parser):
        parser.add_argument('--rows', type=int, default=1500)
        parser.add_argument('--output', type=str, default='data/feedpulse_synthetic_dataset.csv')

    def handle(self, *args, **options):
        rows = options['rows']
        output = options['output']
        anomaly_count = 0
        start_ts = datetime(2026, 1, 1, 6, 0, 0)

        fieldnames = [
            'timestamp', 'factory', 'line_id', 'product_type',
            'temperature', 'machine_speed', 'vibration_level', 'energy_consumption',
            'production_quality_score', 'humidity', 'pressure', 'production_volume',
            'optimal_condition', 'is_anomaly', 'anomaly_reason',
        ]

        with open(output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for i in range(rows):
                ts = start_ts + timedelta(hours=i)
                factory = random.choice(FACTORIES)
                line_id = random.choice(LINES)
                product_type = random.choice(PRODUCT_TYPES)

                is_anomaly = random.random() < 0.09
                if is_anomaly:
                    scenario = random.choice(list(ANOMALY_SCENARIOS.keys()))
                    ranges = ANOMALY_SCENARIOS[scenario]
                    anomaly_count += 1
                else:
                    scenario = 'NORMAL'
                    ranges = NORMAL_RANGES

                row = {
                    'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                    'factory': factory,
                    'line_id': line_id,
                    'product_type': product_type,
                    'temperature': _rand(*ranges['temperature']),
                    'machine_speed': _rand(*ranges['machine_speed']),
                    'vibration_level': _rand(*ranges['vibration_level']),
                    'energy_consumption': _rand(*ranges['energy_consumption']),
                    'production_quality_score': _rand(*ranges['production_quality_score']),
                    'humidity': _rand(*ranges['humidity']),
                    'pressure': _rand(*ranges['pressure']),
                    'production_volume': _rand(*ranges['production_volume']),
                    'optimal_condition': 0 if is_anomaly else 1,
                    'is_anomaly': 1 if is_anomaly else 0,
                    'anomaly_reason': scenario if is_anomaly else '',
                }
                writer.writerow(row)

        rate = round(anomaly_count / rows * 100, 1)
        self.stdout.write(self.style.SUCCESS(
            f"Oluşturuldu: {rows} satır → {output} | Anomali: {anomaly_count} ({rate}%)"
        ))
