# Streamlit BI Prototype Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand `app.py` into a BI-style Streamlit dashboard that keeps the existing choropleth and adds ENGINEER.md-aligned pages using `MASTER_MERGED_CLEANED_DASHBOARD.csv` and cluster data under `data/processed/`.

**Architecture:** Keep a single Streamlit entrypoint in `app.py` to match the current project pattern. Add pure data-preparation helpers for dashboard metrics, time series, correlations, and priority tables so behavior can be tested without launching Streamlit. Use tab-based pages to mirror Looker Studio/Tableau report pages.

**Tech Stack:** Python, pandas, Streamlit, Plotly, pytest, existing GeoJSON and CSV files.

---

## File Structure

- Modify: `app.py`
  - Keep existing choropleth helpers.
  - Add main dataset loading from `MASTER_MERGED_CLEANED_DASHBOARD.csv`.
  - Add helper functions for KPI, trend, correlation, priority, and profile outputs.
  - Replace single-page render with BI-style `st.tabs()` layout.
- Modify: `tests/test_streamlit_dashboard.py`
  - Keep existing tests.
  - Add tests for main dataset preparation, KPI aggregation, trend aggregation, correlation-ready data, and priority table.

---

### Task 1: Add main dashboard data preparation

**Files:**
- Modify: `app.py`
- Modify: `tests/test_streamlit_dashboard.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_streamlit_dashboard.py`:

```python
def test_prepare_main_data_normalizes_codes_and_numeric_columns():
    raw = pd.DataFrame(
        {
            "kode_kemendagri": [3201],
            "nama_clean": ["KABUPATEN BOGOR"],
            "tahun": ["2013"],
            "jumlah_banjir": ["19"],
            "total_hujan_tahunan_mm": ["3343.8"],
            "total_hari_hujan_ekstrem": ["4"],
            "jumlah_sampah_ton_per_tahun": ["1000.5"],
            "total_terdampak": ["895"],
            "pengungsi": ["10"],
            "lat": ["-6.5971"],
            "lon": ["106.806"],
        }
    )

    prepared = app.prepare_main_data(raw)

    assert prepared.loc[0, "kode_kemendagri"] == "3201"
    assert prepared.loc[0, "tahun"] == 2013
    assert prepared.loc[0, "jumlah_banjir"] == 19
    assert prepared.loc[0, "total_hujan_tahunan_mm"] == 3343.8
    assert prepared.loc[0, "jumlah_sampah_ton_per_tahun"] == 1000.5
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_streamlit_dashboard.py::test_prepare_main_data_normalizes_codes_and_numeric_columns -v
```

Expected: FAIL with `AttributeError: module 'dashboard_app' has no attribute 'prepare_main_data'`.

- [ ] **Step 3: Implement minimal code**

In `app.py`, add near path constants:

```python
MAIN_DATA_PATH = Path("MASTER_MERGED_CLEANED_DASHBOARD.csv")
```

Add after `prepare_summary_data`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/test_streamlit_dashboard.py::test_prepare_main_data_normalizes_codes_and_numeric_columns -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_streamlit_dashboard.py
git commit -m "feat: load main dashboard dataset"
```

---

### Task 2: Add KPI and trend aggregations

**Files:**
- Modify: `app.py`
- Modify: `tests/test_streamlit_dashboard.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_streamlit_dashboard.py`:

```python
def test_build_kpis_summarizes_core_engineer_metrics():
    df = pd.DataFrame(
        {
            "kode_kemendagri": ["3201", "3202"],
            "jumlah_banjir": [10, 5],
            "total_terdampak": [100, 50],
            "pengungsi": [20, 5],
            "total_hari_hujan_ekstrem": [3, 2],
            "jumlah_sampah_ton_per_tahun": [1000.0, 500.0],
        }
    )

    kpis = app.build_kpis(df, high_risk_count=4)

    assert kpis["total_banjir"] == 15
    assert kpis["total_terdampak"] == 150
    assert kpis["total_pengungsi"] == 25
    assert kpis["avg_hari_hujan_ekstrem"] == 2.5
    assert kpis["avg_sampah_ton"] == 750.0
    assert kpis["wilayah_risiko_tinggi"] == 4


def test_build_yearly_trend_groups_by_year():
    df = pd.DataFrame(
        {
            "tahun": [2020, 2020, 2021],
            "jumlah_banjir": [1, 2, 3],
            "total_hujan_tahunan_mm": [100.0, 300.0, 500.0],
            "total_terdampak": [10, 20, 30],
        }
    )

    trend = app.build_yearly_trend(df)

    assert trend["tahun"].tolist() == [2020, 2021]
    assert trend["jumlah_banjir"].tolist() == [3, 3]
    assert trend["total_hujan_tahunan_mm"].tolist() == [200.0, 500.0]
    assert trend["total_terdampak"].tolist() == [30, 30]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_streamlit_dashboard.py::test_build_kpis_summarizes_core_engineer_metrics tests/test_streamlit_dashboard.py::test_build_yearly_trend_groups_by_year -v
```

Expected: FAIL with missing function attributes.

- [ ] **Step 3: Implement minimal code**

Add to `app.py` after `load_main_data`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest tests/test_streamlit_dashboard.py::test_build_kpis_summarizes_core_engineer_metrics tests/test_streamlit_dashboard.py::test_build_yearly_trend_groups_by_year -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_streamlit_dashboard.py
git commit -m "feat: add dashboard KPI and trend aggregations"
```

---

### Task 3: Add correlation and priority helper tables

**Files:**
- Modify: `app.py`
- Modify: `tests/test_streamlit_dashboard.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_streamlit_dashboard.py`:

```python
def test_build_correlation_data_aggregates_wilayah_level_metrics():
    main_df = pd.DataFrame(
        {
            "kode_kemendagri": ["3201", "3201", "3202"],
            "nama_clean": ["BOGOR", "BOGOR", "SUKABUMI"],
            "jumlah_banjir": [10, 20, 5],
            "total_hari_hujan_ekstrem": [2, 4, 1],
            "jumlah_sampah_ton_per_tahun": [100.0, 300.0, 50.0],
            "total_terdampak": [100, 200, 25],
        }
    )
    summary_df = pd.DataFrame(
        {
            "kode_kemendagri": ["3201", "3202"],
            "cluster_label": ["Tinggi", "Rendah"],
            "skor_kerentanan_rata2": [0.9, -0.5],
        }
    )

    corr = app.build_correlation_data(main_df, summary_df)

    bogor = corr[corr["kode_kemendagri"] == "3201"].iloc[0]
    assert bogor["avg_jumlah_banjir"] == 15.0
    assert bogor["avg_total_hari_hujan_ekstrem"] == 3.0
    assert bogor["avg_jumlah_sampah_ton_per_tahun"] == 200.0
    assert bogor["total_terdampak"] == 300
    assert bogor["cluster_label"] == "Tinggi"


def test_build_priority_table_sorts_high_risk_first():
    summary_df = pd.DataFrame(
        {
            "nama_clean": ["A", "B", "C"],
            "cluster_label": ["Sedang", "Tinggi", "Rendah"],
            "skor_kerentanan_rata2": [0.2, 0.9, -0.4],
            "avg_jumlah_banjir": [5, 12, 1],
            "avg_total_hari_hujan_ekstrem": [3, 5, 1],
            "avg_jumlah_sampah_ton_per_tahun": [100, 500, 50],
        }
    )

    priority = app.build_priority_table(summary_df)

    assert priority["nama_clean"].tolist()[0] == "B"
    assert priority["prioritas"].tolist() == ["Prioritas 1", "Prioritas 2", "Prioritas 3"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_streamlit_dashboard.py::test_build_correlation_data_aggregates_wilayah_level_metrics tests/test_streamlit_dashboard.py::test_build_priority_table_sorts_high_risk_first -v
```

Expected: FAIL with missing function attributes.

- [ ] **Step 3: Implement minimal code**

Add to `app.py` after `build_yearly_trend`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
pytest tests/test_streamlit_dashboard.py::test_build_correlation_data_aggregates_wilayah_level_metrics tests/test_streamlit_dashboard.py::test_build_priority_table_sorts_high_risk_first -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_streamlit_dashboard.py
git commit -m "feat: add correlation and priority data helpers"
```

---

### Task 4: Render BI-style Streamlit tabs

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Manually verify current app entrypoint**

Run:

```bash
python -m py_compile app.py
```

Expected: exits with code 0.

- [ ] **Step 2: Replace `render_app` with tabbed dashboard implementation**

Replace the current `render_app` function in `app.py` with:

```python
def render_app() -> None:
    st.set_page_config(page_title="Dashboard Risiko Banjir Jawa Barat", layout="wide")
    st.title("Dashboard Risiko Banjir Jawa Barat")
    st.caption(
        "Prototype BI sebelum migrasi ke Looker Studio/Tableau. Dataset utama: "
        "MASTER_MERGED_CLEANED_DASHBOARD.csv; cluster: data/processed/."
    )

    main_df = load_main_data()
    summary_df = load_summary_data()
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

        cluster_counts = (
            filtered_summary["cluster_label"].astype(str).value_counts().reindex(CLUSTER_ORDER, fill_value=0).reset_index()
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
            px.line(peak, x="tahun", y="total_hari_hujan_ekstrem", markers=True, title="Indikator Puncak Bahaya: Hari Hujan Ekstrem"),
            use_container_width=True,
        )

    with tab_corr:
        st.subheader("Korelasi Sampah-Banjir-Cuaca")
        corr = build_correlation_data(filtered_main, summary_df)
        st.plotly_chart(
            px.scatter(
                corr,
                x="avg_jumlah_sampah_ton_per_tahun",
                y="avg_jumlah_banjir",
                size="total_terdampak",
                color="cluster_label",
                color_discrete_map=COLOR_MAP,
                hover_name="nama_clean",
                title="Volume Sampah vs Rata-rata Kejadian Banjir",
            ),
            use_container_width=True,
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
        profile = pd.read_csv("data/processed/cluster_profile.csv")
        st.plotly_chart(
            px.bar(
                profile,
                x="cluster_label",
                y=["avg_jumlah_banjir", "avg_total_hari_hujan_ekstrem"],
                barmode="group",
                title="Profil Rata-rata Indikator per Cluster",
            ),
            use_container_width=True,
        )
        st.dataframe(profile, use_container_width=True, hide_index=True)
        st.dataframe(build_priority_table(filtered_summary), use_container_width=True, hide_index=True)

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
```

- [ ] **Step 3: Compile app**

Run:

```bash
python -m py_compile app.py
```

Expected: exits with code 0.

- [ ] **Step 4: Run dashboard smoke command**

Run:

```bash
streamlit run app.py --server.headless true --server.port 8501
```

Expected: Streamlit starts and serves the app. Stop with `Ctrl+C` after startup is confirmed.

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat: render BI-style dashboard tabs"
```

---

### Task 5: Final verification

**Files:**
- Verify only.

- [ ] **Step 1: Run full dashboard tests**

Run:

```bash
pytest tests/test_streamlit_dashboard.py -v
```

Expected: all tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```bash
pytest -v
```

Expected: all tests pass.

- [ ] **Step 3: Run Python compile check**

Run:

```bash
python -m py_compile app.py
```

Expected: exits with code 0.

- [ ] **Step 4: Manual dashboard review**

Run:

```bash
streamlit run app.py
```

Expected: app opens with six tabs: Executive Summary, Peta Risiko Wilayah, Tren & Puncak Bahaya, Korelasi Sampah-Banjir-Cuaca, Profil Cluster & Prioritas, Metodologi.

- [ ] **Step 5: Commit verification notes if files changed**

If no files changed, skip. If formatting or minor fixes were needed:

```bash
git add app.py tests/test_streamlit_dashboard.py
git commit -m "test: verify streamlit dashboard prototype"
```

---

## Self-Review

- Spec coverage: choropleth retained in Tab 2; ENGINEER.md requirements covered by executive KPIs, risk map, trend/puncak bahaya, correlation, BPBD/Pemda priority table, public/metodologi explanation.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: helper names used by tests match helper names defined in `app.py`.
- Migration feasibility: visuals are BI-common primitives: scorecards, bar charts, line charts, scatter plots, map, and tables.
