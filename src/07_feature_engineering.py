#!/usr/bin/env python3
"""Add analytical features to data/clean/master_merged.csv."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

CLEAN = Path("data/clean")
MASTER = CLEAN / "master_merged.csv"
OUT = CLEAN / "master_merged.csv"

DAMAGE_COLS = [
    "korban_meninggal",
    "korban_hilang",
    "korban_luka",
    "pengungsi",
]


def kategori_hujan(mm):
    if pd.isna(mm):
        return pd.NA
    if mm < 1500:
        return "Rendah (<1500mm)"
    if mm < 2500:
        return "Sedang (1500-2500mm)"
    if mm < 4000:
        return "Tinggi (2500-4000mm)"
    return "Sangat Tinggi (>4000mm)"


def main() -> None:
    df = pd.read_csv(MASTER, dtype={"kode_kemendagri": str, "bps_kode": str})

    rename = {
        "latitude": "lat",
        "longitude": "lon",
        "precipitation_sum_mm": "total_hujan_tahunan_mm",
        "max_daily_precipitation_mm": "max_hujan_harian_mm",
        "heavy_rain_days_50mm": "total_hari_hujan_ekstrem",
        "soil_moisture_0_to_7cm_avg": "avg_kelembaban_tanah",
        "Meninggal": "korban_meninggal",
        "Hilang": "korban_hilang",
        "luka_sakit": "korban_luka",
        "menderita_mengungsi": "pengungsi",
        "Rumah Rusak Berat": "rusak_berat",
        "Rumah Rusak Sedang": "rusak_sedang",
        "Rumah Rusak Ringan": "rusak_ringan",
        "jumlah_sampah_tahunan": "jumlah_sampah_ton_per_hari",
    }
    df = df.rename(columns=rename)

    df["is_sampah_missing"] = df["jumlah_sampah_ton_per_hari"].isna()

    df["rasio_banjir_per_hujan"] = df.apply(
        lambda r: r["jumlah_banjir"] / r["total_hujan_tahunan_mm"]
        if pd.notna(r.get("jumlah_banjir"))
        and pd.notna(r.get("total_hujan_tahunan_mm"))
        and r["total_hujan_tahunan_mm"] > 0
        else pd.NA,
        axis=1,
    )
    df["rasio_banjir_per_hujan"] = pd.to_numeric(df["rasio_banjir_per_hujan"], errors="coerce")
    df.loc[~df["rasio_banjir_per_hujan"].map(lambda x: math.isfinite(x) if pd.notna(x) else True), "rasio_banjir_per_hujan"] = pd.NA

    df["kategori_hujan"] = df["total_hujan_tahunan_mm"].apply(kategori_hujan)
    df["rank_banjir_di_wilayah"] = df.groupby("kode_kemendagri")["jumlah_banjir"].rank(ascending=False, method="dense")

    for col in DAMAGE_COLS:
        if col not in df.columns:
            df[col] = 0
    df["total_terdampak"] = df[DAMAGE_COLS].fillna(0).sum(axis=1)

    preferred = [
        "kode_kemendagri", "nama_clean", "nama_singkat", "tipe", "lat", "lon", "bps_kode", "tahun",
        "jumlah_banjir", "total_hujan_tahunan_mm", "rain_sum_mm", "precipitation_hours_total",
        "rainy_days", "total_hari_hujan_ekstrem", "max_hujan_harian_mm", "wind_gusts_10m_max_kmh",
        "et0_fao_evapotranspiration_mm_avg", "avg_kelembaban_tanah", "rain_intensity_mm_per_hour_avg",
        "jumlah_kejadian_bnpb", "korban_meninggal", "korban_hilang", "korban_luka", "pengungsi",
        "rusak_berat", "rusak_sedang", "rusak_ringan", "Rumah Terendam", "Satuan Pendidikan Rusak",
        "Rumah Ibadat Rusak", "Fasilitas Pelayanan Kesehatan Rusak", "Kantor Rusak", "Jembatan Rusak",
        "satuan", "jumlah_sampah_ton_per_hari", "is_sampah_missing", "rasio_banjir_per_hujan",
        "kategori_hujan", "rank_banjir_di_wilayah", "total_terdampak",
    ]
    cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
    df = df[cols].sort_values(["kode_kemendagri", "tahun"])

    df.to_csv(OUT, index=False)
    print(f"WRITE {OUT} rows={len(df)} cols={len(df.columns)}")


if __name__ == "__main__":
    main()
