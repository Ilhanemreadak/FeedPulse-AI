#!/bin/sh
set -e

echo "==> [FeedPulse] Migration calistiriliyor..."
python manage.py migrate --noinput

echo "==> [FeedPulse] Static dosyalar toplaniyor..."
python manage.py collectstatic --noinput

# Veritabaninda kayit var mi? (Django 4.2 'shell -c' desteklemez,
# bu yuzden python -c + exit code kullaniyoruz)
echo "==> [FeedPulse] Veri kontrol ediliyor..."
if python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','feedpulse_ai.settings'); django.setup(); from operations.models import ProductionRecord; import sys; sys.exit(0 if ProductionRecord.objects.exists() else 1)"; then
    echo "==> [FeedPulse] Veri zaten mevcut, import atlandi."
else
    echo "==> [FeedPulse] Veri yok, dataset import ediliyor..."
    python manage.py import_dataset data/Manufacturing_dataset.csv
fi

# Model var mi?
if [ -f "ml_models/anomaly_model.joblib" ]; then
    echo "==> [FeedPulse] Model zaten mevcut, egitim atlandi."
else
    echo "==> [FeedPulse] Model yok, egitiliyor (birkac dakika surebilir)..."
    python manage.py train_anomaly_model
fi

echo "==> [FeedPulse] Gunicorn baslatiliyor (0.0.0.0:8000)..."
exec gunicorn feedpulse_ai.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
