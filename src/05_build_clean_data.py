#!/usr/bin/env python3
"""Build clean analytical CSV files from raw flood, weather, impact, and waste data."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
CLEAN = Path("data/clean")
REF = Path("data/reference/master_wilayah_jabar.csv")


def kode4(series: pd.Series) -> pd.Series:
    return series.astype(float).astype(int).astype(str).str.zfill(4)


def load_ref() -> pd.DataFrame:
    return pd.read_csv(REF, dtype={"kode_kemendagri": str, "bps_kode": str})


def build_banjir(ref: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(RAW / "banjir_kab_opendata_jabar.csv")
    out = df.assign(kode_kemendagri=kode4(df["kode_kabupaten_kota"]))[
        ["kode_kemendagri", "tahun", "jumlah_banjir"]
    ]
    out = out.groupby(["kode_kemendagri", "tahun"], as_index=False).sum(numeric_only=True)
    out = ref[["kode_kemendagri", "nama_clean", "tipe"]].merge(out, on="kode_kemendagri", how="right")
    return out.sort_values(["kode_kemendagri", "tahun"])


def daily_weather_frame(path: Path) -> pd.DataFrame:
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = data["metadata_wilayah"]
    daily = pd.DataFrame(data["daily"])
    daily["tanggal"] = pd.to_datetime(daily.pop("time"))
    daily["kode_kemendagri"] = meta["kode_kemendagri"]
    daily["nama_clean"] = meta["nama_clean"]

    hourly = pd.DataFrame(data.get("hourly", {}))
    if not hourly.empty and "soil_moisture_0_to_7cm" in hourly:
        hourly["tanggal"] = pd.to_datetime(hourly["time"]).dt.date
        soil = hourly.groupby("tanggal", as_index=False)["soil_moisture_0_to_7cm"].mean()
        soil["tanggal"] = pd.to_datetime(soil["tanggal"])
        daily = daily.merge(soil, on="tanggal", how="left")
    return daily


def build_cuaca_bulanan() -> pd.DataFrame:
    frames = [daily_weather_frame(p) for p in sorted((RAW / "cuaca_raw").glob("*.json"))]
    df = pd.concat(frames, ignore_index=True)
    df["tahun"] = df["tanggal"].dt.year
    df["bulan"] = df["tanggal"].dt.month
    df["rain_intensity_mm_per_hour"] = df["precipitation_sum"] / df["precipitation_hours"].replace({0: pd.NA})

    agg = df.groupby(["kode_kemendagri", "nama_clean", "tahun", "bulan"], as_index=False).agg(
        precipitation_sum_mm=("precipitation_sum", "sum"),
        rain_sum_mm=("rain_sum", "sum"),
        precipitation_hours_total=("precipitation_hours", "sum"),
        rainy_days=("precipitation_sum", lambda s: int((s > 0).sum())),
        heavy_rain_days_50mm=("precipitation_sum", lambda s: int((s >= 50).sum())),
        max_daily_precipitation_mm=("precipitation_sum", "max"),
        wind_gusts_10m_max_kmh=("wind_gusts_10m_max", "max"),
        et0_fao_evapotranspiration_mm_avg=("et0_fao_evapotranspiration", "mean"),
        soil_moisture_0_to_7cm_avg=("soil_moisture_0_to_7cm", "mean"),
        rain_intensity_mm_per_hour_avg=("rain_intensity_mm_per_hour", "mean"),
    )
    return agg.sort_values(["kode_kemendagri", "tahun", "bulan"])


def build_dampak(ref: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(RAW / "200_dampak_bencana.csv")
    df = df[df["Jenis Bencana"].astype(str).str.upper().eq("BANJIR")].copy()
    df["kode_kemendagri"] = (df["Kode Kabupaten"].astype(float) * 100).round().astype(int).astype(str).str.zfill(4)
    cols_sum = [
        "Jumlah Kejadian", "Meninggal", "Hilang", "Luka / Sakit", "menderita_mengungsi",
        "Rumah Rusak Berat", "Rumah Rusak Sedang", "Rumah Rusak Ringan", "Rumah Terendam",
        "Satuan Pendidikan Rusak", "Rumah Ibadat Rusak", "Fasilitas Pelayanan Kesehatan Rusak",
        "Kantor Rusak", "Jembatan Rusak",
    ]
    out = df.groupby(["kode_kemendagri", "Tahun"], as_index=False)[cols_sum].sum()
    out = out.rename(columns={
        "Tahun": "tahun",
        "Jumlah Kejadian": "jumlah_kejadian_bnpb",
        "Luka / Sakit": "luka_sakit",
    })
    out = ref[["kode_kemendagri", "nama_clean", "tipe"]].merge(out, on="kode_kemendagri", how="right")
    return out.sort_values(["kode_kemendagri", "tahun"])


def build_sampah(ref: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(RAW / "sampah_opendata_jabar.csv")
    out = df.assign(kode_kemendagri=kode4(df["kode_kabupaten_kota"]))[
        ["kode_kemendagri", "tahun", "jumlah_sampah", "satuan"]
    ]
    out = out.groupby(["kode_kemendagri", "tahun", "satuan"], as_index=False).sum(numeric_only=True)
    out = out.rename(columns={"jumlah_sampah": "jumlah_sampah_tahunan"})
    out = ref[["kode_kemendagri", "nama_clean", "tipe"]].merge(out, on="kode_kemendagri", how="right")
    return out.sort_values(["kode_kemendagri", "tahun"])


def build_master(ref: pd.DataFrame, banjir: pd.DataFrame, cuaca: pd.DataFrame, dampak: pd.DataFrame, sampah: pd.DataFrame) -> pd.DataFrame:
    cuaca_tahun = cuaca.groupby(["kode_kemendagri", "tahun"], as_index=False).agg(
        precipitation_sum_mm=("precipitation_sum_mm", "sum"),
        rain_sum_mm=("rain_sum_mm", "sum"),
        precipitation_hours_total=("precipitation_hours_total", "sum"),
        rainy_days=("rainy_days", "sum"),
        heavy_rain_days_50mm=("heavy_rain_days_50mm", "sum"),
        max_daily_precipitation_mm=("max_daily_precipitation_mm", "max"),
        wind_gusts_10m_max_kmh=("wind_gusts_10m_max_kmh", "max"),
        et0_fao_evapotranspiration_mm_avg=("et0_fao_evapotranspiration_mm_avg", "mean"),
        soil_moisture_0_to_7cm_avg=("soil_moisture_0_to_7cm_avg", "mean"),
        rain_intensity_mm_per_hour_avg=("rain_intensity_mm_per_hour_avg", "mean"),
    )
    keys = ["kode_kemendagri", "tahun"]
    base = banjir[[*keys, "jumlah_banjir"]].merge(cuaca_tahun, on=keys, how="outer")
    base = base.merge(dampak.drop(columns=["nama_clean", "tipe"], errors="ignore"), on=keys, how="outer")
    base = base.merge(sampah.drop(columns=["nama_clean", "tipe"], errors="ignore"), on=keys, how="outer")
    base = ref.merge(base, on="kode_kemendagri", how="right")
    return base.sort_values(["kode_kemendagri", "tahun"])


def main() -> None:
    CLEAN.mkdir(parents=True, exist_ok=True)
    ref = load_ref()
    banjir = build_banjir(ref)
    cuaca = build_cuaca_bulanan()
    dampak = build_dampak(ref)
    sampah = build_sampah(ref)
    master = build_master(ref, banjir, cuaca, dampak, sampah)

    outputs = {
        "banjir_tahunan.csv": banjir,
        "cuaca_bulanan.csv": cuaca,
        "dampak_clean.csv": dampak,
        "sampah_tahunan.csv": sampah,
        "master_merged.csv": master,
    }
    for name, df in outputs.items():
        path = CLEAN / name
        df.to_csv(path, index=False)
        print(f"WRITE {path} rows={len(df)} cols={len(df.columns)}")


if __name__ == "__main__":
    main()
