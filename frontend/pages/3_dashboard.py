"""
EV/AV data dashboard using sample seed data.
"""
import pandas as pd
import streamlit as st
from frontend.components.charts import ev_adoption_chart, charging_infra_bar, av_safety_gauge

st.title("AV/EV Market Dashboards")

# ── EV Adoption Chart ──────────────────────────────────────────────
st.subheader("Global EV adoption")
try:
    df_ev = pd.read_csv("data/seeds/ev_market_data.csv")
    st.plotly_chart(ev_adoption_chart(df_ev), use_container_width=True)
except FileNotFoundError:
    st.info("Seed data not found. Run `make ingest` first or add data/seeds/ev_market_data.csv")

# ── Charging Infrastructure ────────────────────────────────────────
st.subheader("Charging infrastructure")
charger_data = pd.DataFrame({
    "country":          ["Norway","Netherlands","China","USA","Germany","Nigeria"],
    "charger_type":     ["Fast DC","Fast DC","Fast DC","Fast DC","Fast DC","Fast DC"],
    "chargers_per_100k":[143, 89, 61, 28, 34, 2],
})
st.plotly_chart(charging_infra_bar(charger_data), use_container_width=True)

# ── AV Safety Gauge ────────────────────────────────────────────────
st.subheader("AV safety indicator")
col1, col2 = st.columns([1, 2])
with col1:
    incidents = st.number_input("Incidents per million miles", min_value=0.0, max_value=10.0, value=1.8, step=0.1)
with col2:
    st.plotly_chart(av_safety_gauge(incidents), use_container_width=True)
