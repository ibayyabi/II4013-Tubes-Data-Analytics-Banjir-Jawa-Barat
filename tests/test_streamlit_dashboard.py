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


def test_prepare_main_data_normalizes_codes_and_numeric_columns():
    raw = pd.DataFrame(
        {
            "kode_kemendagri": [3201],
            "nama_clean": ["KABUPATEN BOGOR"],
            "tahun": ["2013"],
            "jumlah_banjir": ["19"],
            "total_hujan_tahunan_mm": ["3343.8"],
            "total_hari_hujan_ekstrem": ["4"],
            "jumlah_sampah_ton_per_tahun": ["1000.5"],
            "total_terdampak": ["895"],
            "pengungsi": ["10"],
            "lat": ["-6.5971"],
            "lon": ["106.806"],
        }
    )

    prepared = app.prepare_main_data(raw)

    assert prepared.loc[0, "kode_kemendagri"] == "3201"
    assert prepared.loc[0, "tahun"] == 2013
    assert prepared.loc[0, "jumlah_banjir"] == 19
    assert prepared.loc[0, "total_hujan_tahunan_mm"] == 3343.8
    assert prepared.loc[0, "jumlah_sampah_ton_per_tahun"] == 1000.5


def test_build_kpis_summarizes_core_engineer_metrics():
    df = pd.DataFrame(
        {
            "kode_kemendagri": ["3201", "3202"],
            "jumlah_banjir": [10, 5],
            "total_terdampak": [100, 50],
            "pengungsi": [20, 5],
            "total_hari_hujan_ekstrem": [3, 2],
            "jumlah_sampah_ton_per_tahun": [1000.0, 500.0],
        }
    )

    kpis = app.build_kpis(df, high_risk_count=4)

    assert kpis["total_banjir"] == 15
    assert kpis["total_terdampak"] == 150
    assert kpis["total_pengungsi"] == 25
    assert kpis["avg_hari_hujan_ekstrem"] == 2.5
    assert kpis["avg_sampah_ton"] == 750.0
    assert kpis["wilayah_risiko_tinggi"] == 4


def test_build_yearly_trend_groups_by_year():
    df = pd.DataFrame(
        {
            "tahun": [2020, 2020, 2021],
            "jumlah_banjir": [1, 2, 3],
            "total_hujan_tahunan_mm": [100.0, 300.0, 500.0],
            "total_terdampak": [10, 20, 30],
        }
    )

    trend = app.build_yearly_trend(df)

    assert trend["tahun"].tolist() == [2020, 2021]
    assert trend["jumlah_banjir"].tolist() == [3, 3]
    assert trend["total_hujan_tahunan_mm"].tolist() == [200.0, 500.0]
    assert trend["total_terdampak"].tolist() == [30, 30]


def test_build_correlation_data_aggregates_wilayah_level_metrics():
    main_df = pd.DataFrame(
        {
            "kode_kemendagri": ["3201", "3201", "3202"],
            "nama_clean": ["BOGOR", "BOGOR", "SUKABUMI"],
            "jumlah_banjir": [10, 20, 5],
            "total_hari_hujan_ekstrem": [2, 4, 1],
            "jumlah_sampah_ton_per_tahun": [100.0, 300.0, 50.0],
            "total_terdampak": [100, 200, 25],
        }
    )
    summary_df = pd.DataFrame(
        {
            "kode_kemendagri": ["3201", "3202"],
            "cluster_label": ["Tinggi", "Rendah"],
            "skor_kerentanan_rata2": [0.9, -0.5],
        }
    )

    corr = app.build_correlation_data(main_df, summary_df)

    bogor = corr[corr["kode_kemendagri"] == "3201"].iloc[0]
    assert bogor["avg_jumlah_banjir"] == 15.0
    assert bogor["avg_total_hari_hujan_ekstrem"] == 3.0
    assert bogor["avg_jumlah_sampah_ton_per_tahun"] == 200.0
    assert bogor["total_terdampak"] == 300
    assert bogor["cluster_label"] == "Tinggi"


def test_build_priority_table_sorts_high_risk_first():
    summary_df = pd.DataFrame(
        {
            "nama_clean": ["A", "B", "C"],
            "cluster_label": ["Sedang", "Tinggi", "Rendah"],
            "skor_kerentanan_rata2": [0.2, 0.9, -0.4],
            "avg_jumlah_banjir": [5, 12, 1],
            "avg_total_hari_hujan_ekstrem": [3, 5, 1],
            "avg_jumlah_sampah_ton_per_tahun": [100, 500, 50],
        }
    )

    priority = app.build_priority_table(summary_df)

    assert priority["nama_clean"].tolist()[0] == "B"
    assert priority["prioritas"].tolist() == ["Prioritas 1", "Prioritas 2", "Prioritas 3"]
