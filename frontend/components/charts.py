"""Reusable Plotly chart components for the dashboard page."""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def ev_adoption_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.line(
        df,
        x="year",
        y="ev_share_pct",
        color="region",
        title="EV market share by region (%)",
        labels={"ev_share_pct": "EV share (%)", "year": "Year"},
        template="plotly_white",
    )
    fig.update_layout(legend_title="Region")
    return fig


def charging_infra_bar(df: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        df,
        x="country",
        y="chargers_per_100k",
        color="charger_type",
        barmode="group",
        title="Public chargers per 100k population",
        template="plotly_white",
    )
    return fig


def av_safety_gauge(incidents_per_million_miles: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=incidents_per_million_miles,
        title={"text": "AV incidents per million miles"},
        gauge={
            "axis": {"range": [0, 10]},
            "bar": {"color": "#1D9E75"},
            "steps": [
                {"range": [0, 2],  "color": "#d4edda"},
                {"range": [2, 5],  "color": "#fff3cd"},
                {"range": [5, 10], "color": "#f8d7da"},
            ],
        },
    ))
    return fig
