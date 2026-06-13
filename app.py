import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

SUMMARY_PATH = Path("data/processed/cluster_wilayah_summary.csv")
GEOJSON_PATH = Path("data/reference/Jabar_By_Kab.geojson")
CLUSTER_ORDER = ["Rendah", "Sedang", "Tinggi"]
COLOR_MAP = {"Rendah": "#FEE8C8", "Sedang": "#FDBB84", "Tinggi": "#E34A33"}
GEOJSON_KEY_CANDIDATES = [
    "kode_kemendagri",
    "KODE_KAB",
    "ID_KAB",
    "kode",
    "id",
    "bps_kode",
    "KABKOTNO",
]


def normalize_region_code(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    if text.isdigit() and len(text) == 2:
        text = f"32{text}"
    return text.zfill(4)


def prepare_summary_data(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "kode_kemendagri",
        "nama_clean",
        "skor_kerentanan_rata2",
        "avg_jumlah_banjir",
        "avg_total_hari_hujan_ekstrem",
        "avg_jumlah_sampah_ton_per_tahun",
        "cluster_label",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required summary columns: {missing}")

    prepared = df.copy()
    prepared["kode_kemendagri"] = prepared["kode_kemendagri"].map(normalize_region_code)
    prepared["cluster_label"] = pd.Categorical(
        prepared["cluster_label"], categories=CLUSTER_ORDER, ordered=True
    )
    return prepared.sort_values("skor_kerentanan_rata2", ascending=False).reset_index(drop=True)


def detect_geojson_key(geojson: dict) -> str:
    features = geojson.get("features", [])
    if not features:
        raise ValueError("GeoJSON has no features")
    properties = features[0].get("properties", {})
    for candidate in GEOJSON_KEY_CANDIDATES:
        if candidate in properties:
            return candidate
    raise ValueError(
        "GeoJSON join key not found. Expected one of: "
        + ", ".join(GEOJSON_KEY_CANDIDATES)
    )


def normalize_geojson_join_key(geojson: dict, key: str) -> dict:
    normalized = json.loads(json.dumps(geojson))
    for feature in normalized.get("features", []):
        props = feature.setdefault("properties", {})
        props["kode_kemendagri_norm"] = normalize_region_code(props.get(key))
    return normalized


def load_summary_data(path: Path = SUMMARY_PATH) -> pd.DataFrame:
    return prepare_summary_data(pd.read_csv(path, dtype={"kode_kemendagri": str}))


def load_geojson(path: Path = GEOJSON_PATH) -> tuple[dict, str]:
    with path.open(encoding="utf-8") as f:
        geojson = json.load(f)
    key = detect_geojson_key(geojson)
    return normalize_geojson_join_key(geojson, key), key


def build_choropleth(df: pd.DataFrame, geojson: dict):
    fig = px.choropleth_mapbox(
        df,
        geojson=geojson,
        locations="kode_kemendagri",
        featureidkey="properties.kode_kemendagri_norm",
        color="cluster_label",
        color_discrete_map=COLOR_MAP,
        category_orders={"cluster_label": CLUSTER_ORDER},
        hover_name="nama_clean",
        hover_data={
            "kode_kemendagri": True,
            "cluster_label": True,
            "skor_kerentanan_rata2": ":.3f",
            "avg_jumlah_banjir": ":.2f",
            "avg_total_hari_hujan_ekstrem": ":.2f",
            "avg_jumlah_sampah_ton_per_tahun": ":,.0f",
        },
        mapbox_style="carto-positron",
        center={"lat": -6.9, "lon": 107.6},
        zoom=7,
        opacity=0.82,
    )
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        legend_title_text="Cluster Kerentanan",
        height=620,
    )
    return fig


def render_metrics(df: pd.DataFrame) -> None:
    counts = df["cluster_label"].value_counts().reindex(CLUSTER_ORDER, fill_value=0)
    cols = st.columns(3)
    for col, label in zip(cols, CLUSTER_ORDER):
        col.metric(label=f"Wilayah {label}", value=int(counts[label]))


def render_app() -> None:
    st.set_page_config(page_title="Kerentanan Banjir Jawa Barat", layout="wide")
    st.title("Choropleth Kerentanan Banjir Jawa Barat")
    st.caption(
        "Summary clustering 2015–2023 berbasis histori banjir, cuaca, dan kapasitas lingkungan."
    )

    df = load_summary_data()
    geojson, geojson_key = load_geojson()

    render_metrics(df)
    st.info(f"Peta memakai join key GeoJSON `{geojson_key}` yang dinormalisasi ke `kode_kemendagri`.")

    st.subheader("Peta Cluster Kerentanan")
    fig = build_choropleth(df, geojson)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Ranking Wilayah Paling Rentan")
    ranking = df[
        [
            "nama_clean",
            "cluster_label",
            "skor_kerentanan_rata2",
            "avg_jumlah_banjir",
            "avg_total_hari_hujan_ekstrem",
            "avg_jumlah_sampah_ton_per_tahun",
        ]
    ].copy()
    st.dataframe(
        ranking,
        use_container_width=True,
        hide_index=True,
        column_config={
            "nama_clean": "Wilayah",
            "cluster_label": "Cluster",
            "skor_kerentanan_rata2": st.column_config.NumberColumn("Skor", format="%.3f"),
            "avg_jumlah_banjir": st.column_config.NumberColumn("Rata-rata Banjir", format="%.2f"),
            "avg_total_hari_hujan_ekstrem": st.column_config.NumberColumn("Rata-rata Hari Hujan Ekstrem", format="%.2f"),
            "avg_jumlah_sampah_ton_per_tahun": st.column_config.NumberColumn("Rata-rata Sampah (ton/tahun)", format="%.0f"),
        },
    )


if __name__ == "__main__":
    render_app()
