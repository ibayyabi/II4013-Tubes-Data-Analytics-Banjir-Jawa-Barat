#!/usr/bin/env python3
"""Export final workbook matching PRD_IMPROVE tab structure."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
CLEAN = Path("data/clean")
REF = Path("data/reference")
OUT = Path("flood-analytics-jabar.xlsx")

TABS = {
    "RAW_banjir_kejadian": RAW / "banjir_kab_opendata_jabar.csv",
    "RAW_cuaca_harian": CLEAN / "cuaca_bulanan.csv",
    "RAW_dampak_bnpb": RAW / "200_dampak_bencana.csv",
    "RAW_sampah_tahunan": RAW / "sampah_opendata_jabar.csv",
    "REF_master_wilayah": REF / "master_wilayah_jabar.csv",
    "CLEAN_banjir_tahunan": CLEAN / "banjir_tahunan.csv",
    "CLEAN_cuaca_bulanan": CLEAN / "cuaca_bulanan.csv",
    "CLEAN_dampak": CLEAN / "dampak_clean.csv",
    "CLEAN_sampah_tahunan": CLEAN / "sampah_tahunan.csv",
    "MASTER_MERGED": CLEAN / "master_merged.csv",
}


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path, dtype={"kode_kemendagri": str, "bps_kode": str})


def main() -> None:
    with pd.ExcelWriter(OUT, engine="openpyxl") as writer:
        for tab, path in TABS.items():
            if not path.exists():
                raise FileNotFoundError(path)
            df = read_table(path)
            df.to_excel(writer, sheet_name=tab[:31], index=False)
            print(f"WRITE tab={tab} rows={len(df)} cols={len(df.columns)}")
    print(f"DONE {OUT}")


if __name__ == "__main__":
    main()
