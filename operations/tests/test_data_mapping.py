import pandas as pd

from operations.services.data_mapping_service import map_columns, normalize_column_name


def test_normalize_strips_units_and_punctuation():
    assert normalize_column_name('Temperature (°C)') == 'temperature_c'
    assert normalize_column_name('Machine Speed (RPM)') == 'machine_speed_rpm'
    assert normalize_column_name('  Energy   Consumption  ') == 'energy_consumption'


def test_map_columns_renames_known_variants():
    df = pd.DataFrame(columns=['Temperature (°C)', 'Machine Speed (RPM)', 'Quality'])
    mapped = map_columns(df)
    assert 'temperature' in mapped.columns
    assert 'machine_speed' in mapped.columns
    assert 'production_quality_score' in mapped.columns


def test_map_columns_leaves_unknown_columns_untouched():
    df = pd.DataFrame(columns=['some_unknown_column'])
    mapped = map_columns(df)
    assert 'some_unknown_column' in mapped.columns
