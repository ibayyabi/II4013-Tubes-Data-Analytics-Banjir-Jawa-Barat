#!/usr/bin/env python3
"""Validate cleaned outputs against PRD_IMPROVE checklist."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CLEAN = Path("data/clean")
REF = Path("data/reference/master_wilayah_jabar.csv")


def fail(msg: str) -> None:
    raise AssertionError(msg)


def assert_unique(df: pd.DataFrame, cols: list[str], name: str) -> None:
    dup = df.duplicated(cols).sum()
    if dup:
        fail(f"{name}: duplicate {cols} = {dup}")


def main() -> None:
    ref = pd.read_csv(REF, dtype={"kode_kemendagri": str})
    master = pd.read_csv(CLEAN / "master_merged.csv", dtype={"kode_kemendagri": str, "bps_kode": str})
    banjir = pd.read_csv(CLEAN / "banjir_tahunan.csv", dtype={"kode_kemendagri": str})
    cuaca = pd.read_csv(CLEAN / "cuaca_bulanan.csv", dtype={"kode_kemendagri": str})
    sampah = pd.read_csv(CLEAN / "sampah_tahunan.csv", dtype={"kode_kemendagri": str})

    if ref["kode_kemendagri"].nunique() != 27:
        fail("REF_master_wilayah must contain 27 wilayah")
    if set(master["kode_kemendagri"].dropna()) - set(ref["kode_kemendagri"]):
        fail("MASTER_MERGED contains kode outside reference")

    assert_unique(master, ["kode_kemendagri", "tahun"], "MASTER_MERGED")
    assert_unique(banjir, ["kode_kemendagri", "tahun"], "banjir_tahunan")
    assert_unique(sampah, ["kode_kemendagri", "tahun"], "sampah_tahunan")
    assert_unique(cuaca, ["kode_kemendagri", "tahun", "bulan"], "cuaca_bulanan")

    if cuaca.query("2012 <= tahun <= 2023")["kode_kemendagri"].nunique() != 27:
        fail("CLEAN_cuaca_bulanan missing wilayah for 2012-2023")
    if master[["lat", "lon"]].isna().any().any():
        fail("MASTER_MERGED has missing lat/lon")
    if "is_sampah_missing" not in master.columns:
        fail("MASTER_MERGED missing is_sampah_missing")
    if pd.isna(master.loc[master["tahun"].between(2012, 2023), "total_hujan_tahunan_mm"]).all():
        fail("MASTER_MERGED weather features are empty")

    print("VALIDATION OK")
    print(f"master rows={len(master)} wilayah={master['kode_kemendagri'].nunique()} tahun={int(master['tahun'].min())}-{int(master['tahun'].max())}")


if __name__ == "__main__":
    main()
