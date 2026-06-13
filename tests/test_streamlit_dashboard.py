import importlib.util
from pathlib import Path

import pandas as pd

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
spec = importlib.util.spec_from_file_location("dashboard_app", APP_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def test_prepare_summary_data_stringifies_code_and_orders_cluster():
    raw = pd.DataFrame(
        {
            "kode_kemendagri": [3201, 3273],
            "nama_clean": ["KABUPATEN BOGOR", "KOTA BANDUNG"],
            "skor_kerentanan_rata2": [0.5, -0.2],
            "avg_jumlah_banjir": [10, 2],
            "avg_total_hari_hujan_ekstrem": [3, 1],
            "avg_jumlah_sampah_ton_per_tahun": [1000, 500],
            "cluster_label": ["Tinggi", "Rendah"],
            "cluster_color": ["#E34A33", "#FEE8C8"],
        }
    )

    prepared = app.prepare_summary_data(raw)

    assert prepared["kode_kemendagri"].tolist() == ["3201", "3273"]
    assert list(prepared["cluster_label"].cat.categories) == ["Rendah", "Sedang", "Tinggi"]


def test_detect_geojson_key_finds_common_property():
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"KODE_KAB": "3201"}, "geometry": None}
        ],
    }

    assert app.detect_geojson_key(geojson) == "KODE_KAB"


def test_detect_geojson_key_raises_clear_error_when_missing():
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"NAME": "BOGOR"}, "geometry": None}
        ],
    }

    try:
        app.detect_geojson_key(geojson)
    except ValueError as exc:
        assert "GeoJSON join key not found" in str(exc)
    else:
        raise AssertionError("detect_geojson_key should raise ValueError")
