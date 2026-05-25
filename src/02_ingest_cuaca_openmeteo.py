#!/usr/bin/env python3
"""Fetch historical daily weather for West Java regencies/cities from Open-Meteo."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

try:
    import requests_cache
except ImportError:  # cache is optional, but recommended
    requests_cache = None

REF_PATH = Path("data/reference/master_wilayah_jabar.csv")
OUT_DIR = Path("data/raw/cuaca_raw")
CACHE_DIR = Path("data/raw/.cache")

START_DATE = "2012-01-01"
END_DATE = "2023-12-31"
ENDPOINT = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARS = [
    "precipitation_sum",
    "rain_sum",
    "precipitation_hours",
    "wind_gusts_10m_max",
    "et0_fao_evapotranspiration",
]
HOURLY_VARS = [
    # Open-Meteo archive exposes soil moisture as hourly, not daily.
    "soil_moisture_0_to_7cm",
]


def slugify(name: str) -> str:
    return name.lower().replace(" ", "_").replace("/", "_")


def make_session() -> requests.Session:
    if requests_cache is None:
        return requests.Session()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return requests_cache.CachedSession(
        str(CACHE_DIR / "openmeteo_cache"),
        expire_after=-1,
    )


def fetch_one(session: requests.Session, row: pd.Series) -> dict[str, Any]:
    params = {
        "latitude": float(row["latitude"]),
        "longitude": float(row["longitude"]),
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": DAILY_VARS,
        "hourly": HOURLY_VARS,
        "timezone": "Asia/Jakarta",
    }
    for attempt in range(1, 6):
        response = session.get(ENDPOINT, params=params, timeout=120)
        if response.status_code != 429:
            response.raise_for_status()
            break
        wait_seconds = 60 * attempt
        print(f"RATE_LIMIT wait {wait_seconds}s")
        time.sleep(wait_seconds)
    else:
        response.raise_for_status()

    payload = response.json()
    payload["metadata_wilayah"] = {
        "kode_kemendagri": str(row["kode_kemendagri"]),
        "nama_clean": row["nama_clean"],
        "nama_singkat": row["nama_singkat"],
        "tipe": row["tipe"],
        "latitude_request": float(row["latitude"]),
        "longitude_request": float(row["longitude"]),
        "periode_start": START_DATE,
        "periode_end": END_DATE,
        "daily_variables_requested": DAILY_VARS,
        "hourly_variables_requested": HOURLY_VARS,
    }
    return payload


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wilayah = pd.read_csv(REF_PATH, dtype={"kode_kemendagri": str, "bps_kode": str})
    session = make_session()

    for _, row in wilayah.iterrows():
        kode = str(row["kode_kemendagri"])
        name = slugify(str(row["nama_singkat"]))
        out_path = OUT_DIR / f"{kode}_{name}.json"

        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"SKIP {out_path}")
            continue

        print(f"FETCH {kode} {row['nama_clean']}")
        payload = fetch_one(session, row)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        time.sleep(10)

    files = sorted(OUT_DIR.glob("*.json"))
    print(f"Selesai. File cuaca: {len(files)} di {OUT_DIR}")


if __name__ == "__main__":
    main()
