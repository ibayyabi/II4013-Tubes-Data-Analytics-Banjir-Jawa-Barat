from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

INPUT_PATH = Path("data/processed/MASTER_MERGED_CLEANED_DASHBOARD.csv")
OUTPUT_DIR = Path("data/processed")
YEARLY_OUTPUT = OUTPUT_DIR / "cluster_tahunan_2015_2023.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "cluster_wilayah_summary.csv"
PROFILE_OUTPUT = OUTPUT_DIR / "cluster_profile.csv"

IDENTITY_COLUMNS = ["kode_kemendagri", "nama_clean", "tahun", "lat", "lon"]
FEATURE_COLUMNS = [
    "jumlah_banjir",
    "jumlah_kejadian_bnpb",
    "rasio_banjir_per_hujan",
    "total_hujan_tahunan_mm",
    "rainy_days",
    "total_hari_hujan_ekstrem",
    "max_hujan_harian_mm",
    "rain_intensity_mm_per_hour_avg",
    "avg_kelembaban_tanah",
    "et0_fao_evapotranspiration_mm_avg",
    "jumlah_sampah_ton_per_tahun",
]
RISK_DIRECTIONS = {
    "jumlah_banjir": 1,
    "jumlah_kejadian_bnpb": 1,
    "rasio_banjir_per_hujan": 1,
    "total_hujan_tahunan_mm": 1,
    "rainy_days": 1,
    "total_hari_hujan_ekstrem": 1,
    "max_hujan_harian_mm": 1,
    "rain_intensity_mm_per_hour_avg": 1,
    "avg_kelembaban_tanah": 1,
    "et0_fao_evapotranspiration_mm_avg": -1,
    "jumlah_sampah_ton_per_tahun": 1,
}
LABEL_ORDER = ["Rendah", "Sedang", "Tinggi"]
COLOR_MAP = {"Rendah": "#FEE8C8", "Sedang": "#FDBB84", "Tinggi": "#E34A33"}


def validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in IDENTITY_COLUMNS + FEATURE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def prepare_model_data(df: pd.DataFrame) -> pd.DataFrame:
    validate_columns(df)
    prepared = df.loc[df["tahun"].between(2015, 2023), IDENTITY_COLUMNS + FEATURE_COLUMNS].copy()
    prepared["kode_kemendagri"] = prepared["kode_kemendagri"].astype(str).str.zfill(4)
    prepared["tahun"] = prepared["tahun"].astype(int)
    for col in FEATURE_COLUMNS:
        prepared[col] = pd.to_numeric(prepared[col], errors="coerce")
    return prepared.reset_index(drop=True)


def scale_features(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    imputed = imputer.fit_transform(df[FEATURE_COLUMNS])
    scaled = scaler.fit_transform(imputed)
    scaled_df = pd.DataFrame(scaled, columns=FEATURE_COLUMNS, index=df.index)
    return scaled_df, scaled


def compute_vulnerability_score(scaled_features: pd.DataFrame) -> pd.Series:
    directional = scaled_features.copy()
    for col, direction in RISK_DIRECTIONS.items():
        directional[col] = directional[col] * direction
    return directional.mean(axis=1)


def assign_cluster_labels(yearly: pd.DataFrame) -> pd.DataFrame:
    cluster_scores = yearly.groupby("cluster_id_raw")["skor_kerentanan"].mean().sort_values()
    label_map = {cluster_id: LABEL_ORDER[idx] for idx, cluster_id in enumerate(cluster_scores.index)}
    result = yearly.copy()
    result["cluster_label"] = result["cluster_id_raw"].map(label_map)
    result["cluster_color"] = result["cluster_label"].map(COLOR_MAP)
    return result


def run_kmeans(prepared: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    scaled_df, scaled_array = scale_features(prepared)
    model = KMeans(n_clusters=3, random_state=42, n_init=20)
    cluster_ids = model.fit_predict(scaled_array)

    yearly = prepared.copy()
    yearly["cluster_id_raw"] = cluster_ids
    yearly["skor_kerentanan"] = compute_vulnerability_score(scaled_df)
    yearly = assign_cluster_labels(yearly)

    score = silhouette_score(scaled_array, cluster_ids)
    return yearly, float(score)


def dominant_label(labels: pd.Series) -> str:
    counts = labels.value_counts()
    if counts.empty:
        return "Rendah"
    tied = counts[counts == counts.max()].index.tolist()
    priority = {"Rendah": 1, "Sedang": 2, "Tinggi": 3}
    return sorted(tied, key=lambda label: priority[label])[0]


def build_region_summary(yearly: pd.DataFrame) -> pd.DataFrame:
    grouped = yearly.groupby(["kode_kemendagri", "nama_clean", "lat", "lon"], as_index=False)
    summary = grouped.agg(
        skor_kerentanan_rata2=("skor_kerentanan", "mean"),
        avg_jumlah_banjir=("jumlah_banjir", "mean"),
        avg_total_hari_hujan_ekstrem=("total_hari_hujan_ekstrem", "mean"),
        avg_jumlah_sampah_ton_per_tahun=("jumlah_sampah_ton_per_tahun", "mean"),
    )
    dominant = grouped["cluster_label"].agg(dominant_label).rename(columns={"cluster_label": "cluster_label"})
    summary = summary.merge(dominant, on=["kode_kemendagri", "nama_clean", "lat", "lon"], how="left")
    summary["cluster_dominan"] = summary["cluster_label"]
    summary["cluster_color"] = summary["cluster_label"].map(COLOR_MAP)
    return summary.sort_values("skor_kerentanan_rata2", ascending=False).reset_index(drop=True)


def build_cluster_profile(yearly: pd.DataFrame, silhouette: float) -> pd.DataFrame:
    profile = yearly.groupby("cluster_label", as_index=False).agg(
        jumlah_observasi=("cluster_label", "size"),
        avg_skor_kerentanan=("skor_kerentanan", "mean"),
        avg_jumlah_banjir=("jumlah_banjir", "mean"),
        avg_jumlah_kejadian_bnpb=("jumlah_kejadian_bnpb", "mean"),
        avg_total_hujan_tahunan_mm=("total_hujan_tahunan_mm", "mean"),
        avg_total_hari_hujan_ekstrem=("total_hari_hujan_ekstrem", "mean"),
        avg_max_hujan_harian_mm=("max_hujan_harian_mm", "mean"),
        avg_kelembaban_tanah=("avg_kelembaban_tanah", "mean"),
        avg_et0=("et0_fao_evapotranspiration_mm_avg", "mean"),
        avg_jumlah_sampah_ton_per_tahun=("jumlah_sampah_ton_per_tahun", "mean"),
    )
    profile["cluster_color"] = profile["cluster_label"].map(COLOR_MAP)
    profile["silhouette_score"] = silhouette
    profile["interpretasi"] = profile["cluster_label"].map(
        {
            "Rendah": "Kerentanan relatif rendah berdasarkan kombinasi banjir, hujan ekstrem, dan sampah.",
            "Sedang": "Kerentanan menengah dengan beberapa indikator risiko meningkat.",
            "Tinggi": "Kerentanan tinggi dengan kombinasi histori banjir, tekanan cuaca, dan sampah lebih berat.",
        }
    )
    order = {label: idx for idx, label in enumerate(LABEL_ORDER)}
    profile["_order"] = profile["cluster_label"].map(order)
    return profile.sort_values("_order").drop(columns="_order").reset_index(drop=True)


def write_outputs(yearly: pd.DataFrame, summary: pd.DataFrame, profile: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yearly.to_csv(YEARLY_OUTPUT, index=False)
    summary.to_csv(SUMMARY_OUTPUT, index=False)
    profile.to_csv(PROFILE_OUTPUT, index=False)


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    prepared = prepare_model_data(df)
    yearly, silhouette = run_kmeans(prepared)
    summary = build_region_summary(yearly)
    profile = build_cluster_profile(yearly, silhouette)
    write_outputs(yearly, summary, profile)

    print(f"Wrote {YEARLY_OUTPUT} ({len(yearly)} rows)")
    print(f"Wrote {SUMMARY_OUTPUT} ({len(summary)} rows)")
    print(f"Wrote {PROFILE_OUTPUT} ({len(profile)} rows)")
    print(f"Silhouette score: {silhouette:.4f}")


if __name__ == "__main__":
    main()
