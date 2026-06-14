import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

SUMMARY_PATH = Path("data/processed/cluster_wilayah_summary.csv")
MAIN_DATA_PATH = Path("MASTER_MERGED_CLEANED_DASHBOARD.csv")
GEOJSON_PATH = Path("data/reference/Jabar_By_Kab.geojson")
MONTHLY_WEATHER_PATH = Path("data/clean/cuaca_bulanan.csv")
ECONOMIC_RISK_PATH = Path("data/raw/grafisk-potensi-banjir-jABAR.csv")
REFERENCE_REGIONS_PATH = Path("data/reference/master_wilayah_jabar.csv")
CLUSTER_ORDER = ["Rendah", "Sedang", "Tinggi"]
MONTH_LABELS = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"}
COLOR_MAP = {"Rendah": "#FEE8C8", "Sedang": "#FDBB84", "Tinggi": "#E34A33"}
READABLE_INK = "#17251F"
GEOJSON_KEY_CANDIDATES = [
    "kode_kemendagri",
    "KODE_KAB",
    "ID_KAB",
    "kode",
    "id",
    "bps_kode",
    "KABKOTNO",
]


def apply_readable_chart_theme(fig):
    fig.update_layout(
        font={"color": READABLE_INK},
        title={"font": {"color": READABLE_INK}},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        coloraxis_colorbar={
            "tickfont": {"color": READABLE_INK},
            "title": {"font": {"color": READABLE_INK}},
        },
    )
    fig.update_xaxes(tickfont={"color": READABLE_INK}, title_font={"color": READABLE_INK})
    fig.update_yaxes(tickfont={"color": READABLE_INK}, title_font={"color": READABLE_INK})
    return fig


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


def prepare_main_data(df: pd.DataFrame) -> pd.DataFrame:
    required = [
        "kode_kemendagri",
        "nama_clean",
        "tahun",
        "jumlah_banjir",
        "total_hujan_tahunan_mm",
        "total_hari_hujan_ekstrem",
        "jumlah_sampah_ton_per_tahun",
        "total_terdampak",
        "pengungsi",
        "lat",
        "lon",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required main dashboard columns: {missing}")

    prepared = df.copy()
    prepared["kode_kemendagri"] = prepared["kode_kemendagri"].map(normalize_region_code)
    numeric_columns = [
        "tahun",
        "jumlah_banjir",
        "total_hujan_tahunan_mm",
        "total_hari_hujan_ekstrem",
        "jumlah_sampah_ton_per_tahun",
        "total_terdampak",
        "pengungsi",
        "lat",
        "lon",
    ]
    for column in numeric_columns:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared["tahun"] = prepared["tahun"].astype("Int64")
    return prepared


def load_main_data(path: Path = MAIN_DATA_PATH) -> pd.DataFrame:
    return prepare_main_data(pd.read_csv(path, dtype={"kode_kemendagri": str}))


def build_kpis(df: pd.DataFrame, high_risk_count: int) -> dict:
    return {
        "total_banjir": int(df["jumlah_banjir"].fillna(0).sum()),
        "total_terdampak": int(df["total_terdampak"].fillna(0).sum()),
        "total_pengungsi": int(df["pengungsi"].fillna(0).sum()),
        "avg_hari_hujan_ekstrem": float(df["total_hari_hujan_ekstrem"].mean()),
        "avg_sampah_ton": float(df["jumlah_sampah_ton_per_tahun"].mean()),
        "wilayah_risiko_tinggi": int(high_risk_count),
    }


def build_yearly_trend(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("tahun", as_index=False)
        .agg(
            jumlah_banjir=("jumlah_banjir", "sum"),
            total_hujan_tahunan_mm=("total_hujan_tahunan_mm", "mean"),
            total_terdampak=("total_terdampak", "sum"),
        )
        .sort_values("tahun")
    )


def prepare_monthly_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    required = ["kode_kemendagri", "nama_clean", "tahun", "bulan", "rain_sum_mm", "heavy_rain_days_50mm", "max_daily_precipitation_mm"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required monthly weather columns: {missing}")
    prepared = df.copy()
    prepared["kode_kemendagri"] = prepared["kode_kemendagri"].map(normalize_region_code)
    for column in ["tahun", "bulan", "rain_sum_mm", "heavy_rain_days_50mm", "max_daily_precipitation_mm"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    prepared["bulan_label"] = prepared["bulan"].map(MONTH_LABELS)
    return prepared


def build_monthly_hazard(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["bulan", "bulan_label"], as_index=False)
        .agg(
            rain_sum_mm=("rain_sum_mm", "mean"),
            heavy_rain_days_50mm=("heavy_rain_days_50mm", "sum"),
            max_daily_precipitation_mm=("max_daily_precipitation_mm", "max"),
        )
        .sort_values("bulan")
    )


def build_correlation_data(main_df: pd.DataFrame, summary_df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        main_df.groupby(["kode_kemendagri", "nama_clean"], as_index=False)
        .agg(
            avg_jumlah_banjir=("jumlah_banjir", "mean"),
            avg_total_hari_hujan_ekstrem=("total_hari_hujan_ekstrem", "mean"),
            avg_jumlah_sampah_ton_per_tahun=("jumlah_sampah_ton_per_tahun", "mean"),
            total_terdampak=("total_terdampak", "sum"),
        )
    )
    return grouped.merge(
        summary_df[["kode_kemendagri", "cluster_label", "skor_kerentanan_rata2"]],
        on="kode_kemendagri",
        how="left",
    )


def build_quadrant_data(corr_df: pd.DataFrame) -> pd.DataFrame:
    median_sampah = corr_df["avg_jumlah_sampah_ton_per_tahun"].median()
    median_banjir = corr_df["avg_jumlah_banjir"].median()
    data = corr_df.copy()
    high_waste = data["avg_jumlah_sampah_ton_per_tahun"] >= median_sampah
    high_flood = data["avg_jumlah_banjir"] >= median_banjir
    data["kuadran_risiko"] = "Monitoring"
    data.loc[high_waste & ~high_flood, "kuadran_risiko"] = "Beban Lingkungan"
    data.loc[~high_waste & high_flood, "kuadran_risiko"] = "Risiko Hidrometeorologi"
    data.loc[high_waste & high_flood, "kuadran_risiko"] = "Prioritas Drainase"
    data.attrs["median_sampah"] = median_sampah
    data.attrs["median_banjir"] = median_banjir
    return data


def build_priority_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    priority_rank = {"Tinggi": 1, "Sedang": 2, "Rendah": 3}
    priority_label = {"Tinggi": "Prioritas 1", "Sedang": "Prioritas 2", "Rendah": "Prioritas 3"}
    table = summary_df.copy()
    table["_priority_rank"] = table["cluster_label"].astype(str).map(priority_rank).fillna(4)
    table["prioritas"] = table["cluster_label"].astype(str).map(priority_label).fillna("Monitoring")
    return (
        table.sort_values(["_priority_rank", "skor_kerentanan_rata2"], ascending=[True, False])
        .drop(columns=["_priority_rank"])
        .reset_index(drop=True)
    )

CLUSTER_PROFILE_METRICS = {
    "avg_skor_kerentanan": "Skor Kerentanan",
    "avg_jumlah_banjir": "Rata-rata Banjir",
    "avg_total_hari_hujan_ekstrem": "Hari Hujan Ekstrem",
    "avg_jumlah_sampah_ton_per_tahun": "Sampah (ton/tahun)",
}


def build_cluster_profile_heatmap(profile: pd.DataFrame) -> pd.DataFrame:
    required = ["cluster_label", *CLUSTER_PROFILE_METRICS]
    missing = [col for col in required if col not in profile.columns]
    if missing:
        raise ValueError(f"Missing required cluster profile columns: {missing}")

    tidy = profile[required].copy()
    tidy["cluster_label"] = pd.Categorical(tidy["cluster_label"], categories=CLUSTER_ORDER, ordered=True)
    tidy = tidy.sort_values("cluster_label")
    heatmap = tidy.melt(
        id_vars="cluster_label",
        value_vars=list(CLUSTER_PROFILE_METRICS),
        var_name="indikator",
        value_name="nilai",
    )
    heatmap["indikator"] = heatmap["indikator"].map(CLUSTER_PROFILE_METRICS)
    return heatmap.sort_values("cluster_label").reset_index(drop=True)


def build_cluster_cards(profile: pd.DataFrame) -> pd.DataFrame:
    required = [
        "cluster_label",
        "jumlah_observasi",
        "avg_skor_kerentanan",
        "avg_jumlah_banjir",
        "avg_total_hari_hujan_ekstrem",
        "avg_jumlah_sampah_ton_per_tahun",
        "interpretasi",
    ]
    missing = [col for col in required if col not in profile.columns]
    if missing:
        raise ValueError(f"Missing required cluster card columns: {missing}")

    cards = profile[required].copy()
    cards["cluster_label"] = pd.Categorical(cards["cluster_label"], categories=CLUSTER_ORDER, ordered=True)
    return cards.sort_values("cluster_label").reset_index(drop=True)


def load_summary_data(path: Path = SUMMARY_PATH) -> pd.DataFrame:
    return prepare_summary_data(pd.read_csv(path, dtype={"kode_kemendagri": str}))


def load_monthly_weather(path: Path = MONTHLY_WEATHER_PATH) -> pd.DataFrame:
    return prepare_monthly_weather_data(pd.read_csv(path, dtype={"kode_kemendagri": str}))


def prepare_economic_risk_data(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "Category": "nama_singkat",
        "Luas Bahaya(Ha)": "luas_bahaya_ha",
        "Jiwa Terpapar": "jiwa_terpapar",
        "Fisik (Rp. Miliyar)": "fisik_rp_miliar",
        "Ekonomi (Rp. Miliyar)": "ekonomi_rp_miliar",
        "Lingkungan (Ha)": "lingkungan_ha",
    }
    missing = [col for col in rename if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required economic risk columns: {missing}")
    prepared = df.rename(columns=rename).copy()
    prepared["nama_clean"] = prepared["nama_singkat"].astype(str).str.upper().map(lambda x: f"KABUPATEN {x}" if not x.startswith("KOTA") else x)
    for column in ["luas_bahaya_ha", "jiwa_terpapar", "fisik_rp_miliar", "ekonomi_rp_miliar", "lingkungan_ha"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    return prepared


def load_economic_risk(path: Path = ECONOMIC_RISK_PATH) -> pd.DataFrame:
    return prepare_economic_risk_data(pd.read_csv(path))


def load_reference_regions(path: Path = REFERENCE_REGIONS_PATH) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"kode_kemendagri": str})


def build_region_coverage(summary_df: pd.DataFrame, reference_df: pd.DataFrame) -> dict:
    covered = set(summary_df["kode_kemendagri"].map(normalize_region_code))
    expected = set(reference_df["kode_kemendagri"].map(normalize_region_code))
    return {"covered": len(covered & expected), "expected": len(expected), "missing": len(expected - covered)}


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
    st.set_page_config(page_title="Dashboard Risiko Banjir Jawa Barat", layout="wide")
    st.title("Dashboard Risiko Banjir Jawa Barat")
    st.caption(
        "Prototype BI sebelum migrasi ke Looker Studio/Tableau. Dataset utama: "
        "MASTER_MERGED_CLEANED_DASHBOARD.csv; cluster: data/processed/."
    )

    main_df = load_main_data()
    summary_df = load_summary_data()
    monthly_weather = load_monthly_weather()
    economic_risk = load_economic_risk()
    reference_regions = load_reference_regions()
    geojson, geojson_key = load_geojson()

    years = sorted([int(year) for year in main_df["tahun"].dropna().unique()])
    selected_years = st.sidebar.slider(
        "Rentang Tahun",
        min_value=min(years),
        max_value=max(years),
        value=(min(years), max(years)),
    )
    selected_clusters = st.sidebar.multiselect(
        "Cluster Risiko",
        options=CLUSTER_ORDER,
        default=CLUSTER_ORDER,
    )

    filtered_main = main_df[
        main_df["tahun"].between(selected_years[0], selected_years[1])
    ].copy()
    filtered_summary = summary_df[
        summary_df["cluster_label"].astype(str).isin(selected_clusters)
    ].copy()
    filtered_monthly = monthly_weather[
        monthly_weather["tahun"].between(selected_years[0], selected_years[1])
    ].copy()
    coverage = build_region_coverage(summary_df, reference_regions)

    high_risk_count = int((filtered_summary["cluster_label"].astype(str) == "Tinggi").sum())
    kpis = build_kpis(filtered_main, high_risk_count)

    tab_summary, tab_map, tab_trend, tab_corr, tab_cluster, tab_method = st.tabs(
        [
            "Executive Summary",
            "Peta Risiko Wilayah",
            "Tren & Puncak Bahaya",
            "Korelasi Sampah-Banjir-Cuaca",
            "Profil Cluster & Prioritas",
            "Metodologi",
        ]
    )

    with tab_summary:
        st.subheader("Executive Summary")
        cols = st.columns(6)
        cols[0].metric("Total Banjir", f"{kpis['total_banjir']:,}")
        cols[1].metric("Total Terdampak", f"{kpis['total_terdampak']:,}")
        cols[2].metric("Total Pengungsi", f"{kpis['total_pengungsi']:,}")
        cols[3].metric("Wilayah Risiko Tinggi", f"{kpis['wilayah_risiko_tinggi']:,}")
        cols[4].metric("Rata-rata Hari Hujan Ekstrem", f"{kpis['avg_hari_hujan_ekstrem']:.2f}")
        cols[5].metric("Rata-rata Sampah", f"{kpis['avg_sampah_ton']:,.0f} ton")
        st.metric("Cakupan Wilayah", f"{coverage['covered']}/{coverage['expected']} kab/kota", delta=f"{coverage['missing']} belum tercakup")
        st.metric("Potensi Kerugian Ekonomi", f"Rp {economic_risk['ekonomi_rp_miliar'].sum():,.0f} miliar")

        cluster_counts = (
            filtered_summary["cluster_label"]
            .astype(str)
            .value_counts()
            .reindex(CLUSTER_ORDER, fill_value=0)
            .reset_index()
        )
        cluster_counts.columns = ["cluster_label", "jumlah_wilayah"]
        st.plotly_chart(
            px.bar(
                cluster_counts,
                x="cluster_label",
                y="jumlah_wilayah",
                color="cluster_label",
                color_discrete_map=COLOR_MAP,
                title="Jumlah Wilayah per Cluster Risiko",
            ),
            use_container_width=True,
        )
        st.dataframe(
            build_priority_table(filtered_summary).head(5)[
                ["nama_clean", "prioritas", "cluster_label", "skor_kerentanan_rata2", "avg_jumlah_banjir"]
            ],
            use_container_width=True,
            hide_index=True,
        )

    with tab_map:
        st.subheader("Peta Risiko Wilayah")
        render_metrics(filtered_summary)
        st.info(f"Peta memakai join key GeoJSON `{geojson_key}` yang dinormalisasi ke `kode_kemendagri`.")
        st.plotly_chart(build_choropleth(filtered_summary, geojson), use_container_width=True)
        st.dataframe(
            build_priority_table(filtered_summary)[
                [
                    "nama_clean",
                    "prioritas",
                    "cluster_label",
                    "skor_kerentanan_rata2",
                    "avg_jumlah_banjir",
                    "avg_total_hari_hujan_ekstrem",
                    "avg_jumlah_sampah_ton_per_tahun",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    with tab_trend:
        st.subheader("Tren & Puncak Bahaya")
        yearly = build_yearly_trend(filtered_main)
        st.plotly_chart(
            px.line(yearly, x="tahun", y="jumlah_banjir", markers=True, title="Tren Kejadian Banjir Tahunan"),
            use_container_width=True,
        )
        st.plotly_chart(
            px.bar(yearly, x="tahun", y="total_hujan_tahunan_mm", title="Rata-rata Curah Hujan Tahunan"),
            use_container_width=True,
        )
        peak = (
            filtered_main.groupby("tahun", as_index=False)
            .agg(total_hari_hujan_ekstrem=("total_hari_hujan_ekstrem", "sum"))
            .sort_values("tahun")
        )
        st.plotly_chart(
            px.line(peak, x="tahun", y="total_hari_hujan_ekstrem", markers=True, title="Indikator Puncak Bahaya: Hari Hujan Ekstrem Tahunan"),
            use_container_width=True,
        )
        monthly_hazard = build_monthly_hazard(filtered_monthly)
        st.plotly_chart(
            px.bar(monthly_hazard, x="bulan_label", y="heavy_rain_days_50mm", title="Puncak Bahaya Bulanan: Total Hari Hujan Ekstrem >50mm"),
            use_container_width=True,
        )
        st.plotly_chart(
            px.line(monthly_hazard, x="bulan_label", y="max_daily_precipitation_mm", markers=True, title="Curah Hujan Harian Maksimum per Bulan"),
            use_container_width=True,
        )

    with tab_corr:
        st.subheader("Korelasi Sampah-Banjir-Cuaca")
        corr = build_correlation_data(filtered_main, summary_df)
        quadrant = build_quadrant_data(corr)
        fig_quadrant = px.scatter(
            quadrant,
            x="avg_jumlah_sampah_ton_per_tahun",
            y="avg_jumlah_banjir",
            size="total_terdampak",
            color="kuadran_risiko",
            hover_name="nama_clean",
            title="Kuadran Risiko: Sampah vs Frekuensi Banjir",
            labels={
                "avg_jumlah_sampah_ton_per_tahun": "Rata-rata Sampah (ton/tahun)",
                "avg_jumlah_banjir": "Rata-rata Kejadian Banjir",
            },
        )
        fig_quadrant.add_vline(x=quadrant.attrs["median_sampah"], line_dash="dash", annotation_text="Median sampah")
        fig_quadrant.add_hline(y=quadrant.attrs["median_banjir"], line_dash="dash", annotation_text="Median banjir")
        st.plotly_chart(fig_quadrant, use_container_width=True)
        st.dataframe(
            quadrant.sort_values(["kuadran_risiko", "avg_jumlah_banjir"], ascending=[True, False])[
                ["nama_clean", "kuadran_risiko", "avg_jumlah_sampah_ton_per_tahun", "avg_jumlah_banjir", "total_terdampak"]
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.plotly_chart(
            px.scatter(
                corr,
                x="avg_total_hari_hujan_ekstrem",
                y="avg_jumlah_banjir",
                size="total_terdampak",
                color="cluster_label",
                color_discrete_map=COLOR_MAP,
                hover_name="nama_clean",
                title="Hari Hujan Ekstrem vs Rata-rata Kejadian Banjir",
            ),
            use_container_width=True,
        )
        st.dataframe(corr.sort_values("avg_jumlah_banjir", ascending=False), use_container_width=True, hide_index=True)

    with tab_cluster:
        st.subheader("Profil Cluster & Prioritas Wilayah")
        st.caption("Baca karakter tiap cluster lewat indikator utama. Tabel lengkap tetap tersedia di bagian bawah.")
        profile = pd.read_csv("data/processed/cluster_profile.csv")
        heatmap = build_cluster_profile_heatmap(profile)
        st.plotly_chart(
            apply_readable_chart_theme(
                px.imshow(
                    heatmap.pivot(index="indikator", columns="cluster_label", values="nilai"),
                    color_continuous_scale="Greens",
                    aspect="auto",
                    title="Profil Indikator per Cluster",
                    labels={"x": "Cluster", "y": "Indikator", "color": "Nilai"},
                )
            ),
            use_container_width=True,
        )

        st.markdown("**Ringkasan karakter cluster**")
        for column, (_, row) in zip(st.columns(3), build_cluster_cards(profile).iterrows()):
            with column:
                st.metric(str(row["cluster_label"]), f"{row['jumlah_observasi']:.0f} observasi")
                st.markdown(
                    f"""
                    - Skor: **{row['avg_skor_kerentanan']:.2f}**
                    - Banjir: **{row['avg_jumlah_banjir']:.1f}** kejadian
                    - Hujan ekstrem: **{row['avg_total_hari_hujan_ekstrem']:.1f}** hari
                    - Sampah: **{row['avg_jumlah_sampah_ton_per_tahun']:,.0f}** ton/tahun

                    {row['interpretasi']}
                    """
                )

        priority = build_priority_table(filtered_summary)
        st.markdown("**Top 5 wilayah prioritas**")
        st.dataframe(
            priority.head(5)[
                [
                    "nama_clean",
                    "prioritas",
                    "cluster_label",
                    "skor_kerentanan_rata2",
                    "avg_jumlah_banjir",
                    "avg_total_hari_hujan_ekstrem",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("Lihat data lengkap"):
            st.markdown("**Profil cluster mentah**")
            st.dataframe(profile, use_container_width=True, hide_index=True)
            st.markdown("**Prioritas semua wilayah**")
            st.dataframe(priority, use_container_width=True, hide_index=True)
            st.markdown("**Rekomendasi cepat per audience**")
            st.dataframe(
                priority.assign(
                    bpbd="Prioritaskan logistik/evakuasi",
                    pemda="Audit drainase dan tata ruang lokal",
                    publik="Pantau peringatan hujan ekstrem dan siapkan evakuasi mandiri",
                )[["nama_clean", "prioritas", "cluster_label", "bpbd", "pemda", "publik"]],
                use_container_width=True,
                hide_index=True,
            )
            st.markdown("**Potensi dampak ekonomi/fisik**")
            st.dataframe(
                economic_risk.sort_values("ekonomi_rp_miliar", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

    with tab_method:
        st.subheader("Data Dictionary & Metodologi")
        st.markdown(
            """
            **Sumber utama:** OpenDataJabar, DIBI/BNPB, Open-Meteo, dan data olahan pipeline proyek.  
            **Dataset dashboard:** `MASTER_MERGED_CLEANED_DASHBOARD.csv`.  
            **Dataset cluster:** `data/processed/cluster_wilayah_summary.csv`, `cluster_tahunan_2015_2023.csv`, `cluster_profile.csv`.  
            **Unit spasial:** 27 Kabupaten/Kota di Jawa Barat.  
            **Catatan periode:** dokumen ENGINEER.md menargetkan 2012–2024, sedangkan model cluster tersedia untuk 2015–2023. Dashboard menampilkan periode sesuai data utama dan memberi konteks khusus untuk hasil cluster.  
            **Tujuan BI:** struktur tab ini sengaja dibuat setara dengan page/report di Looker Studio atau dashboard sheet di Tableau.
            """
        )


if __name__ == "__main__":
    render_app()
