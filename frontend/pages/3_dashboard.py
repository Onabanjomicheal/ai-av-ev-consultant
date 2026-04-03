"""
AV/EV Consultant Dashboard — powered by real IEA + NHTSA SGO data.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from frontend.components.styles import inject_global_styles

st.set_page_config(layout="wide")
st.title("AV/EV Intelligence Dashboard")
st.markdown("Real-time insights from IEA Global EV Outlook 2025 and NHTSA AV Incident Reports.")
inject_global_styles()
st.markdown(
    """
    <div class="card">
        <strong>Executive-ready snapshots of market movement and safety trends.</strong>
        <div class="tag">IEA</div>
        <div class="tag">NHTSA</div>
        <div class="tag">Trends</div>
    </div>
    """,
    unsafe_allow_html=True,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'seeds')

# ── Data loaders ───────────────────────────────────────────────────

@st.cache_data
def load_ev_data():
    path = os.path.join(DATA_DIR, 'ev_market_data.csv')
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    return df.dropna(subset=['year', 'value'])


@st.cache_data
def load_adas_data():
    path = os.path.join(DATA_DIR, 'SGO-2021-01_Incident_Reports_ADAS.csv')
    df = pd.read_csv(path, low_memory=False, encoding='latin-1')
    df.columns = df.columns.str.strip()
    return df


@st.cache_data
def load_ads_data():
    path = os.path.join(DATA_DIR, 'SGO-2021-01_Incident_Reports_ADS.csv')
    df = pd.read_csv(path, low_memory=False, encoding='latin-1')
    df.columns = df.columns.str.strip()
    return df


# ── Load all data ──────────────────────────────────────────────────

try:
    ev_df = load_ev_data()
    ev_loaded = True
except Exception as e:
    ev_loaded = False
    ev_error = str(e)

try:
    adas_df = load_adas_data()
    ads_df  = load_ads_data()
    av_loaded = True
except Exception as e:
    av_loaded = False
    av_error = str(e)


# ══════════════════════════════════════════════════════════════════
# SECTION 1 — EV MARKET INTELLIGENCE
# ══════════════════════════════════════════════════════════════════

st.header("Electric Vehicle Market Intelligence")

if not ev_loaded:
    st.error(f"Could not load EV data: {ev_error}")
else:
    # ── KPI row ────────────────────────────────────────────────────
    latest_year = int(
        ev_df[ev_df['category'] == 'Historical']['year'].max()
    )
    ev_sales = ev_df[
        (ev_df['parameter'] == 'EV sales') &
        (ev_df['category'] == 'Historical') &
        (ev_df['year'] == latest_year)
    ]['value'].sum()

    ev_stock = ev_df[
        (ev_df['parameter'] == 'EV stock') &
        (ev_df['category'] == 'Historical') &
        (ev_df['year'] == latest_year)
    ]['value'].sum()

    regions = ev_df['region_country'].nunique()

    k1, k2, k3 = st.columns(3)
    k1.metric("Global EV Sales (latest year)", f"{ev_sales/1e6:.1f}M vehicles")
    k2.metric("Global EV Stock (latest year)", f"{ev_stock/1e6:.1f}M vehicles")
    k3.metric("Regions / Countries tracked", f"{regions}")

    st.divider()

    # ── Filters ────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    all_regions = sorted(ev_df['region_country'].dropna().unique().tolist())
    african = [r for r in all_regions if any(
        x in r for x in ['Africa', 'Nigeria', 'Kenya', 'South Africa', 'Egypt', 'Morocco']
    )]
    default_regions = african if african else all_regions[:6]

    with col1:
        selected_regions = st.multiselect(
            "Regions / Countries",
            options=all_regions,
            default=default_regions[:6],
        )
    with col2:
        parameters = sorted(ev_df['parameter'].dropna().unique().tolist())
        selected_param = st.selectbox("Metric", parameters,
            index=parameters.index('EV sales') if 'EV sales' in parameters else 0
        )
    with col3:
        powertrains = sorted(ev_df['powertrain'].dropna().unique().tolist())
        selected_pt = st.multiselect("Powertrain", powertrains, default=powertrains[:2])

    year_min = int(ev_df['year'].min())
    year_max = int(ev_df['year'].max())
    year_range = st.slider("Year range", year_min, year_max, (2015, year_max))

    # ── Chart 1: Trend by region ───────────────────────────────────
    filtered = ev_df[
        (ev_df['region_country'].isin(selected_regions)) &
        (ev_df['parameter'] == selected_param) &
        (ev_df['powertrain'].isin(selected_pt)) &
        (ev_df['year'].between(year_range[0], year_range[1]))
    ].groupby(['region_country', 'year', 'category'])['value'].sum().reset_index()

    if filtered.empty:
        st.info("No data for selected filters. Try adjusting regions or powertrain.")
    else:
        fig1 = px.line(
            filtered,
            x='year', y='value',
            color='region_country',
            line_dash='category',
            title=f"{selected_param} by region — {year_range[0]} to {year_range[1]}",
            labels={'value': 'Vehicles', 'year': 'Year', 'region_country': 'Region'},
            template='plotly_white',
        )
        fig1.update_layout(legend_title="Region (solid=Historical, dash=Projection)")
        st.plotly_chart(fig1, use_container_width=True)

    st.divider()

    # ── Chart 2: BEV vs PHEV comparison ───────────────────────────
    st.subheader("BEV vs PHEV breakdown")

    bev_phev = ev_df[
        (ev_df['parameter'] == 'EV sales') &
        (ev_df['category'] == 'Historical') &
        (ev_df['powertrain'].isin(['BEV', 'PHEV'])) &
        (ev_df['year'].between(year_range[0], year_range[1]))
    ].groupby(['year', 'powertrain'])['value'].sum().reset_index()

    if not bev_phev.empty:
        fig2 = px.bar(
            bev_phev,
            x='year', y='value',
            color='powertrain',
            barmode='group',
            title="Global BEV vs PHEV sales",
            labels={'value': 'Vehicles sold', 'year': 'Year'},
            template='plotly_white',
            color_discrete_map={'BEV': '#1D9E75', 'PHEV': '#378ADD'},
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # ── Chart 3: Africa focus ──────────────────────────────────────
    st.subheader("Africa EV landscape")

    africa_df = ev_df[
        ev_df['region_country'].str.contains('Africa|Nigeria|Kenya|Morocco|Egypt|Ethiopia',
                                              case=False, na=False)
    ]

    if africa_df.empty:
        st.info("No Africa-specific data found. The IEA data may aggregate Africa as a region.")
        africa_df = ev_df[ev_df['region_country'].str.contains('Africa', case=False, na=False)]

    if not africa_df.empty:
        africa_sales = africa_df[
            (africa_df['parameter'] == 'EV sales') &
            (africa_df['category'] == 'Historical')
        ].groupby(['year', 'region_country'])['value'].sum().reset_index()

        if not africa_sales.empty:
            fig3 = px.area(
                africa_sales,
                x='year', y='value',
                color='region_country',
                title="Africa EV sales trend",
                labels={'value': 'Vehicles', 'year': 'Year'},
                template='plotly_white',
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Africa sales data not available in historical records.")
    else:
        st.info("Africa data not found in this dataset.")


# ══════════════════════════════════════════════════════════════════
# SECTION 2 — AV SAFETY INTELLIGENCE
# ══════════════════════════════════════════════════════════════════

st.header("Autonomous Vehicle Safety Intelligence")
st.caption("Source: NHTSA Standing General Order (SGO) Incident Reports")

if not av_loaded:
    st.error(f"Could not load AV incident data: {av_error}")
else:
    # Combine ADAS + ADS
    adas_df['system_type'] = 'ADAS'
    ads_df['system_type']  = 'ADS'
    av_df = pd.concat([adas_df, ads_df], ignore_index=True)

    # ── KPI row ────────────────────────────────────────────────────
    total_incidents = len(av_df)
    injury_col = 'Highest Injury Severity Alleged'
    injuries = av_df[av_df[injury_col].notna()][injury_col].value_counts()
    serious = injuries[injuries.index.str.contains('serious|fatal|injury',
                       case=False, na=False)].sum() if injury_col in av_df.columns else 0
    engaged_col = 'Automation System Engaged?'
    engaged = av_df[av_df[engaged_col] == 'Yes'].shape[0] if engaged_col in av_df.columns else 0

    a1, a2, a3 = st.columns(3)
    a1.metric("Total incidents reported", f"{total_incidents:,}")
    a2.metric("Incidents with system engaged", f"{engaged:,}")
    a3.metric("Serious / fatal injuries", f"{serious:,}")

    st.divider()

    col_a, col_b = st.columns(2)

    # ── Chart 4: Incidents by severity ────────────────────────────
    with col_a:
        if injury_col in av_df.columns:
            sev = av_df[injury_col].value_counts().reset_index()
            sev.columns = ['severity', 'count']
            sev = sev[sev['severity'].notna()]
            fig4 = px.bar(
                sev.head(8),
                x='count', y='severity',
                orientation='h',
                title="Incidents by injury severity",
                template='plotly_white',
                color='count',
                color_continuous_scale='Reds',
            )
            fig4.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig4, use_container_width=True)

    # ── Chart 5: ADAS vs ADS ──────────────────────────────────────
    with col_b:
        sys_count = av_df['system_type'].value_counts().reset_index()
        sys_count.columns = ['system', 'count']
        fig5 = px.pie(
            sys_count,
            names='system', values='count',
            title="ADAS vs ADS incidents",
            template='plotly_white',
            color_discrete_map={'ADAS': '#378ADD', 'ADS': '#1D9E75'},
        )
        st.plotly_chart(fig5, use_container_width=True)

    # ── Chart 6: Incidents by weather ─────────────────────────────
    st.subheader("Incident conditions analysis")

    weather_cols = [c for c in av_df.columns if c.startswith('Weather -') and 'Unknown' not in c and 'Other' not in c]
    if weather_cols:
        weather_counts = {}
        for wc in weather_cols:
            label = wc.replace('Weather - ', '')
            count = av_df[av_df[wc] == 1].shape[0] if av_df[wc].dtype in ['int64', 'float64'] else \
                    av_df[av_df[wc].astype(str).str.upper() == 'YES'].shape[0]
            if count > 0:
                weather_counts[label] = count

        if weather_counts:
            w_df = pd.DataFrame(list(weather_counts.items()), columns=['condition', 'incidents'])
            fig6 = px.bar(
                w_df.sort_values('incidents', ascending=False),
                x='condition', y='incidents',
                title="AV incidents by weather condition",
                template='plotly_white',
                color='incidents',
                color_continuous_scale='Blues',
            )
            fig6.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig6, use_container_width=True)

    # ── Chart 7: Incidents over time ──────────────────────────────
    if 'Report Year' in av_df.columns and 'Report Month' in av_df.columns:
        av_df['Report Year'] = pd.to_numeric(av_df['Report Year'], errors='coerce')
        av_df['Report Month'] = pd.to_numeric(av_df['Report Month'], errors='coerce')
        time_df = av_df.dropna(subset=['Report Year', 'Report Month'])
        time_df = time_df.groupby(['Report Year', 'Report Month', 'system_type']).size().reset_index(name='incidents')
        time_df['date'] = pd.to_datetime(
            time_df[['Report Year', 'Report Month']].rename(
                columns={'Report Year': 'year', 'Report Month': 'month'}
            ).assign(day=1)
        )
        fig7 = px.line(
            time_df.sort_values('date'),
            x='date', y='incidents',
            color='system_type',
            title="AV incident reports over time",
            labels={'incidents': 'Number of incidents', 'date': 'Date'},
            template='plotly_white',
            color_discrete_map={'ADAS': '#378ADD', 'ADS': '#1D9E75'},
        )
        st.plotly_chart(fig7, use_container_width=True)

    # ── Table: Recent incidents ────────────────────────────────────
    st.subheader("Recent incident records")
    # Filters
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        sys_filter = st.multiselect(
            "System type",
            options=sorted(av_df['system_type'].dropna().unique().tolist()),
            default=sorted(av_df['system_type'].dropna().unique().tolist()),
        )
    with f2:
        state_options = (
            sorted(av_df['State'].dropna().astype(str).unique().tolist())
            if 'State' in av_df.columns else []
        )
        state_filter = st.multiselect(
            "State",
            options=state_options,
            default=state_options[:8] if state_options else [],
        )
    with f3:
        year_options = (
            sorted(pd.to_numeric(av_df['Report Year'], errors='coerce').dropna().astype(int).unique().tolist())
            if 'Report Year' in av_df.columns else []
        )
        year_filter = st.multiselect(
            "Report year",
            options=year_options,
            default=year_options[-3:] if len(year_options) >= 3 else year_options,
        )
    with f4:
        severity_options = (
            sorted(av_df['Highest Injury Severity Alleged'].dropna().astype(str).unique().tolist())
            if 'Highest Injury Severity Alleged' in av_df.columns else []
        )
        severity_filter = st.multiselect(
            "Severity",
            options=severity_options,
            default=severity_options,
        )
    display_cols = [c for c in [
        'Report Year', 'Report Month', 'Make', 'Model',
        'system_type', 'Automation System Engaged?',
        'Highest Injury Severity Alleged', 'Crash With', 'State'
    ] if c in av_df.columns]

    filtered_av = av_df.copy()
    if sys_filter:
        filtered_av = filtered_av[filtered_av['system_type'].isin(sys_filter)]
    if state_filter and 'State' in filtered_av.columns:
        filtered_av = filtered_av[filtered_av['State'].astype(str).isin(state_filter)]
    if year_filter and 'Report Year' in filtered_av.columns:
        filtered_av = filtered_av[pd.to_numeric(filtered_av['Report Year'], errors='coerce').isin(year_filter)]
    if severity_filter and 'Highest Injury Severity Alleged' in filtered_av.columns:
        filtered_av = filtered_av[filtered_av['Highest Injury Severity Alleged'].astype(str).isin(severity_filter)]

    st.dataframe(
        filtered_av[display_cols].dropna(how='all').head(50),
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.caption("Data sources: IEA Global EV Outlook 2025 · NHTSA SGO AV Incident Reports 2021")
