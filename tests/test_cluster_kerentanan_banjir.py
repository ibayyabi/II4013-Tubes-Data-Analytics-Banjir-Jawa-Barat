import importlib.util
from pathlib import Path

import pandas as pd

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "src" / "10_cluster_kerentanan_banjir.py"
spec = importlib.util.spec_from_file_location("cluster_kerentanan_banjir", SCRIPT_PATH)
cluster_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cluster_module)


def sample_df():
    rows = []
    for year in range(2014, 2024):
        rows.append(
            {
                "kode_kemendagri": 3201,
                "nama_clean": "KABUPATEN BOGOR",
                "tahun": year,
                "lat": -6.5,
                "lon": 106.8,
                "jumlah_banjir": year - 2014,
                "jumlah_kejadian_bnpb": year - 2013,
                "rasio_banjir_per_hujan": 0.01,
                "total_hujan_tahunan_mm": 2500 + year,
                "rainy_days": 200,
                "total_hari_hujan_ekstrem": 3,
                "max_hujan_harian_mm": 100,
                "rain_intensity_mm_per_hour_avg": 0.8,
                "avg_kelembaban_tanah": 0.45,
                "et0_fao_evapotranspiration_mm_avg": 3.5,
                "jumlah_sampah_ton_per_tahun": 1000 + year,
            }
        )
    return pd.DataFrame(rows)


def test_prepare_model_data_filters_to_2015_2023_and_stringifies_code():
    prepared = cluster_module.prepare_model_data(sample_df())

    assert prepared["tahun"].min() == 2015
    assert prepared["tahun"].max() == 2023
    assert prepared["kode_kemendagri"].iloc[0] == "3201"
    assert len(prepared) == 9


def test_compute_vulnerability_score_inverts_evapotranspiration():
    scaled = pd.DataFrame(
        {
            "jumlah_banjir": [1.0, -1.0],
            "jumlah_kejadian_bnpb": [1.0, -1.0],
            "rasio_banjir_per_hujan": [1.0, -1.0],
            "total_hujan_tahunan_mm": [1.0, -1.0],
            "rainy_days": [1.0, -1.0],
            "total_hari_hujan_ekstrem": [1.0, -1.0],
            "max_hujan_harian_mm": [1.0, -1.0],
            "rain_intensity_mm_per_hour_avg": [1.0, -1.0],
            "avg_kelembaban_tanah": [1.0, -1.0],
            "et0_fao_evapotranspiration_mm_avg": [-1.0, 1.0],
            "jumlah_sampah_ton_per_tahun": [1.0, -1.0],
        }
    )

    scores = cluster_module.compute_vulnerability_score(scaled)

    assert scores.iloc[0] > scores.iloc[1]


def test_build_region_summary_returns_one_row_per_region():
    yearly = pd.DataFrame(
        {
            "kode_kemendagri": ["3201", "3201", "3273"],
            "nama_clean": ["KABUPATEN BOGOR", "KABUPATEN BOGOR", "KOTA BANDUNG"],
            "lat": [-6.5, -6.5, -6.9],
            "lon": [106.8, 106.8, 107.6],
            "tahun": [2021, 2022, 2022],
            "cluster_label": ["Tinggi", "Sedang", "Rendah"],
            "cluster_id_raw": [2, 1, 0],
            "skor_kerentanan": [2.0, 1.0, -1.0],
            "jumlah_banjir": [10, 8, 1],
            "total_hari_hujan_ekstrem": [5, 4, 1],
            "jumlah_sampah_ton_per_tahun": [1000, 1100, 300],
        }
    )

    summary = cluster_module.build_region_summary(yearly)

    assert set(summary["kode_kemendagri"]) == {"3201", "3273"}
    assert summary.loc[summary["kode_kemendagri"] == "3201", "cluster_label"].iloc[0] == "Sedang"
    assert "skor_kerentanan_rata2" in summary.columns
