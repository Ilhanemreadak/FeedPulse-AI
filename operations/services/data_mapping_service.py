import re


COLUMN_MAP = {
    # timestamp
    'timestamp': 'timestamp',
    # temperature variants
    'temperature': 'temperature',
    'temperature_c': 'temperature',        # Temperature (°C)
    'temperature__c': 'temperature',
    'temperature___c': 'temperature',
    'temp': 'temperature',
    # machine speed variants
    'machine_speed': 'machine_speed',
    'machine_speed_rpm': 'machine_speed',  # Machine Speed (RPM)
    'rpm': 'machine_speed',
    'speed': 'machine_speed',
    # vibration
    'vibration_level': 'vibration_level',
    'vibration_level_mm_s': 'vibration_level',  # Vibration Level (mm/s)
    'vibration': 'vibration_level',
    # energy
    'energy_consumption': 'energy_consumption',
    'energy_consumption_kwh': 'energy_consumption',  # Energy Consumption (kWh)
    'energy': 'energy_consumption',
    # quality
    'production_quality_score': 'production_quality_score',
    'quality_score': 'production_quality_score',
    'quality': 'production_quality_score',
    # optimal condition
    'optimal_conditions': 'optimal_condition',
    'optimal_condition': 'optimal_condition',
    # other fields
    'humidity': 'humidity',
    'pressure': 'pressure',
    'production_volume': 'production_volume',
    'volume': 'production_volume',
    'factory': 'factory',
    'line_id': 'line_id',
    'line': 'line_id',
    'product_type': 'product_type',
    'product': 'product_type',
    'is_anomaly': 'is_anomaly',
    'anomaly': 'is_anomaly',
    'fault': 'is_anomaly',
    'failure': 'is_anomaly',
    'target': 'is_anomaly',
    'anomaly_reason': 'anomaly_reason',
}


def normalize_column_name(col):
    col = col.lower()
    col = re.sub(r'[^a-z0-9]', '_', col)
    col = re.sub(r'_+', '_', col)
    col = col.strip('_')
    return col


def map_columns(df):
    rename = {}
    for col in df.columns:
        normalized = normalize_column_name(col)
        if normalized in COLUMN_MAP:
            rename[col] = COLUMN_MAP[normalized]
    return df.rename(columns=rename)
