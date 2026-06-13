# Streamlit Choropleth Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a simple Streamlit MVP dashboard showing flood vulnerability clusters on a Jawa Barat choropleth map.

**Architecture:** Put reusable data-loading and GeoJSON-key helper functions in `app.py` so they can be tested without launching Streamlit. The Streamlit page reads clustering outputs, detects the GeoJSON join key, renders Plotly choropleth, metric cards, and a ranking table.

**Tech Stack:** Python, pandas, Streamlit, Plotly, pytest.

---

## Tasks

1. Add Streamlit and Plotly dependencies.
2. Add tests for dashboard data helpers.
3. Implement `app.py` with helper functions and Streamlit UI.
4. Verify tests and importability.
