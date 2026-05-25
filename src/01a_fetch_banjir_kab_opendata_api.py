"""
Fetch data kejadian bencana banjir berdasarkan kabupaten/kota dari API Open Data Jabar.

Output:
- data/raw/api_opendata_jabar/banjir_kab/page_skip_*.json
- data/raw/api_opendata_jabar/banjir_kab/metadata.json
- data/raw/banjir_kab_opendata_jabar.csv

Jalankan dari root repo:
python src/01a_fetch_banjir_kab_opendata_api.py
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests


BASE_URL = (
    "https://data.jabarprov.go.id/api-backend/bigdata/bpbd/"
    "od_17600_jml_kejadian_bencana_banjir_brdsrkn_kabupatenkota_v1"
)

RAW_JSON_DIR = Path("data/raw/api_opendata_jabar/banjir_kab")
OUTPUT_CSV = Path("data/raw/banjir_kab_opendata_jabar.csv")
METADATA_PATH = RAW_JSON_DIR / "metadata.json"

LIMIT = 100
SLEEP_SECONDS = 0.5
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3


class ResponseStructureError(RuntimeError):
    """Raised when API response structure cannot be parsed into records."""


def extract_records(response_json: Any) -> list[dict[str, Any]]:
    """Extract list records from common Open Data API response shapes."""
    if isinstance(response_json, list):
        return response_json

    if not isinstance(response_json, dict):
        raise ResponseStructureError(f"Response type tidak dikenali: {type(response_json)}")

    direct_keys = ["data", "result", "results", "items", "records", "rows"]
    for key in direct_keys:
        value = response_json.get(key)
        if isinstance(value, list):
            return value

    nested_containers = ["data", "result", "results"]
    nested_keys = ["content", "rows", "items", "records", "data"]
    for container_key in nested_containers:
        container = response_json.get(container_key)
        if isinstance(container, dict):
            for key in nested_keys:
                value = container.get(key)
                if isinstance(value, list):
                    return value

    raise ResponseStructureError(
        f"Struktur response tidak dikenali. Top-level keys: {list(response_json.keys())}"
    )


def fetch_page(skip: int) -> Any:
    """Fetch one API page with retry."""
    params = {"limit": LIMIT, "skip": skip}
    headers = {
        "accept": "application/json",
        "User-Agent": "flood-analytics-jabar/1.0",
    }

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                BASE_URL,
                params=params,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            wait_seconds = attempt * 2
            print(f"Percobaan {attempt}/{MAX_RETRIES} gagal untuk skip={skip}: {exc}")
            if attempt < MAX_RETRIES:
                print(f"Menunggu {wait_seconds} detik sebelum retry...")
                time.sleep(wait_seconds)

    raise RuntimeError(f"Gagal fetch skip={skip} setelah {MAX_RETRIES} percobaan") from last_error


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def main() -> None:
    RAW_JSON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    all_records: list[dict[str, Any]] = []
    skip = 0
    page_count = 0

    while True:
        print(f"Fetching skip={skip}, limit={LIMIT}")
        response_json = fetch_page(skip)

        page_path = RAW_JSON_DIR / f"page_skip_{skip}.json"
        save_json(page_path, response_json)

        records = extract_records(response_json)
        print(f"Records fetched: {len(records)}")

        if not records:
            break

        all_records.extend(records)
        page_count += 1

        if len(records) < LIMIT:
            break

        skip += LIMIT
        time.sleep(SLEEP_SECONDS)

    df = pd.DataFrame(all_records)

    if not df.empty:
        before = len(df)
        df = df.drop_duplicates()
        after = len(df)
        if before != after:
            print(f"Duplikat dihapus: {before - after}")

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    metadata = {
        "source": BASE_URL,
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "limit": LIMIT,
        "pages": page_count,
        "total_records": int(len(df)),
        "output_csv": str(OUTPUT_CSV),
        "raw_json_dir": str(RAW_JSON_DIR),
        "columns": df.columns.tolist(),
    }
    save_json(METADATA_PATH, metadata)

    print("Kolom ditemukan:")
    print(df.columns.tolist())
    print(f"Total rows: {len(df)}")
    print(f"Saved CSV: {OUTPUT_CSV}")
    print(f"Saved metadata: {METADATA_PATH}")


if __name__ == "__main__":
    main()
