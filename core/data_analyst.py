"""
core/data_analyst.py

Pandas-based data query layer for the AV/EV assistant.
When a question is data-oriented, this module:
  1. Detects the intent
  2. Runs the right pandas query against the CSV seeds
  3. Returns a structured result (text summary + dataframe)

The LLM then uses this result as context to write a natural language answer.
"""
from __future__ import annotations
import os
import pandas as pd
from enum import Enum
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'seeds')


# ── Intent types ───────────────────────────────────────────────────

class DataIntent(str, Enum):
    EV_SALES_RANKING     = "ev_sales_ranking"
    EV_SALES_TREND       = "ev_sales_trend"
    EV_STOCK             = "ev_stock"
    EV_CHARGING          = "ev_charging"
    BEV_PHEV_COMPARE     = "bev_phev_compare"
    AV_INCIDENTS         = "av_incidents"
    AV_SEVERITY          = "av_severity"
    AV_WEATHER           = "av_weather"
    AV_TREND             = "av_trend"
    NONE                 = "none"


# ── Keyword classifier ─────────────────────────────────────────────

_INTENT_KEYWORDS = {
    DataIntent.EV_SALES_RANKING: [
        "top", "highest", "most", "ranking", "rank", "leading", "best",
        "largest", "biggest", "compare countries", "which country",
    ],
    DataIntent.EV_SALES_TREND: [
        "trend", "over time", "growth", "increase", "decrease", "year",
        "evolution", "progress", "history", "since", "from 20",
    ],
    DataIntent.EV_STOCK: [
        "stock", "total vehicles", "on road", "fleet", "registered",
    ],
    DataIntent.EV_CHARGING: [
        "charging", "charger", "charge point", "infrastructure",
    ],
    DataIntent.BEV_PHEV_COMPARE: [
        "bev", "phev", "battery electric", "plug-in hybrid", "compare bev",
        "bev vs", "phev vs",
    ],
    DataIntent.AV_INCIDENTS: [
        "incident", "crash", "accident", "collision", "report", "nhtsa",
        "sgo", "autonomous vehicle crash", "av crash", "adas incident",
    ],
    DataIntent.AV_SEVERITY: [
        "injury", "fatal", "severe", "severity", "hurt", "killed", "death",
    ],
    DataIntent.AV_WEATHER: [
        "weather", "rain", "snow", "fog", "clear", "conditions",
    ],
    DataIntent.AV_TREND: [
        "av incident trend", "incidents over time", "crash trend",
        "incident growth", "monthly incidents",
    ],
}

_EV_HINTS = [
    "ev", "electric vehicle", "bev", "phev", "sales", "stock", "charging",
    "charger", "infrastructure", "market", "adoption",
]
_AV_HINTS = [
    "av", "autonomous", "ads", "adas", "incident", "crash", "collision",
    "nhtsa", "sgo", "automation",
]


def classify_data_intent(question: str) -> DataIntent:
    q = question.lower()
    scores = {intent: 0 for intent in DataIntent}
    for intent, keywords in _INTENT_KEYWORDS.items():
        scores[intent] = sum(1 for kw in keywords if kw in q)
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return DataIntent.NONE

    # Require domain hints so generic phrases like "top risks" don't trigger EV charts.
    if best in {
        DataIntent.EV_SALES_RANKING,
        DataIntent.EV_SALES_TREND,
        DataIntent.EV_STOCK,
        DataIntent.EV_CHARGING,
        DataIntent.BEV_PHEV_COMPARE,
    }:
        return best if any(h in q for h in _EV_HINTS) else DataIntent.NONE

    if best in {
        DataIntent.AV_INCIDENTS,
        DataIntent.AV_SEVERITY,
        DataIntent.AV_WEATHER,
        DataIntent.AV_TREND,
    }:
        return best if any(h in q for h in _AV_HINTS) else DataIntent.NONE

    return best


# ── Data loaders ───────────────────────────────────────────────────

def _load_ev() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, 'ev_market_data.csv')
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df['year']  = pd.to_numeric(df['year'],  errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')
    return df.dropna(subset=['year', 'value'])


def _load_ev_countries() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, 'ev_sales_countries.csv')
    raw = pd.read_csv(path, header=None)

    header_idx = None
    for i, val in enumerate(raw.iloc[:, 0].astype(str)):
        if val.strip().lower() == "region_country":
            header_idx = i
            break
    if header_idx is None:
        return pd.DataFrame(columns=["region_country", "year", "value"])

    header_row = raw.iloc[header_idx].tolist()
    data = raw.iloc[header_idx + 1:].copy()
    data = data[data.iloc[:, 0].notna()]
    data = data[data.iloc[:, 0].astype(str).str.strip() != ""]

    year_cols = [str(x).strip() for x in header_row[1:len(data.columns)]]
    data.columns = ["region_country"] + year_cols

    long = data.melt(id_vars="region_country", var_name="year", value_name="value")
    long["year"] = pd.to_numeric(long["year"], errors="coerce")
    long["value"] = (
        long["value"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long.dropna(subset=["region_country", "year", "value"])


def _load_ev_regions() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, 'ev_sales_regions.csv')
    raw = pd.read_csv(path, header=None)

    header_idx = None
    for i, row in raw.iterrows():
        first = str(row.iloc[0]).strip().lower()
        second = str(row.iloc[1]).strip().lower() if len(row) > 1 else ""
        if first == "mode" and second == "region_country":
            header_idx = i
            break
    if header_idx is None:
        return pd.DataFrame(columns=["region_country", "year", "value"])

    header_row = raw.iloc[header_idx].tolist()
    data = raw.iloc[header_idx + 1:].copy()
    data = data[data.iloc[:, 1].notna()]
    data = data[data.iloc[:, 1].astype(str).str.strip() != ""]

    year_cols = [str(x).strip() for x in header_row[2:len(data.columns)]]
    data.columns = ["mode", "region_country"] + year_cols
    data = data.drop(columns=["mode"])

    long = data.melt(id_vars="region_country", var_name="year", value_name="value")
    long["year"] = pd.to_numeric(long["year"], errors="coerce")
    long["value"] = (
        long["value"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    return long.dropna(subset=["region_country", "year", "value"])


def _load_av() -> pd.DataFrame:
    adas_path = os.path.join(DATA_DIR, 'SGO-2021-01_Incident_Reports_ADAS.csv')
    ads_path  = os.path.join(DATA_DIR, 'SGO-2021-01_Incident_Reports_ADS.csv')
    dfs = []
    for path, label in [(adas_path, 'ADAS'), (ads_path, 'ADS')]:
        if os.path.exists(path):
            d = pd.read_csv(path, low_memory=False, encoding='latin-1')
            d.columns = d.columns.str.strip()
            d['system_type'] = label
            dfs.append(d)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


# ── Query functions ────────────────────────────────────────────────

def _extract_year(question: str) -> int | None:
    import re
    match = re.search(r'20[1-2]\d', question)
    return int(match.group()) if match else None


def _extract_region(question: str) -> str | None:
    regions = [
        'china', 'europe', 'usa', 'united states', 'norway', 'germany',
        'france', 'uk', 'india', 'africa', 'nigeria', 'kenya',
        'south africa', 'world', 'global', 'north america',
        'asia pacific', 'middle east', 'caspian',
    ]
    q = question.lower()
    for r in regions:
        if r in q:
            return r.title()
    return None


def _is_country_level(question: str) -> bool:
    q = question.lower()
    if any(k in q for k in ["country", "countries", "nation", "national"]):
        return True

    region = _extract_region(question)
    if not region:
        return False

    country_names = {
        "china", "usa", "united states", "norway", "germany", "france",
        "uk", "india", "nigeria", "kenya", "south africa",
    }
    return region.lower() in country_names


def _is_region_level(question: str) -> bool:
    q = question.lower()
    if any(k in q for k in ["region", "regional", "continent"]):
        return True
    return any(k in q for k in [
        "africa", "europe", "north america", "asia pacific",
        "middle east", "caspian", "world", "global",
    ])


def _select_sales_df(question: str) -> pd.DataFrame:
    if _is_country_level(question):
        return _load_ev_countries()
    if _is_region_level(question):
        return _load_ev_regions()
    return _load_ev()


def query_ev_sales_ranking(question: str) -> dict:
    df = _select_sales_df(question)
    if "category" in df.columns:
        default_year = int(df[df['category'] == 'Historical']['year'].max())
    else:
        default_year = int(df['year'].max()) if not df.empty else None
    year = _extract_year(question) or default_year

    if "category" in df.columns and "parameter" in df.columns:
        filtered = df[
            (df['parameter'] == 'EV sales') &
            (df['category'] == 'Historical') &
            (df['year'] == year)
        ]
    else:
        filtered = df[df['year'] == year]

    result = (
        filtered
        .groupby('region_country')['value']
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    result.columns = ['Region / Country', 'EV Sales (vehicles)']
    result['EV Sales (vehicles)'] = result['EV Sales (vehicles)'].astype(int)

    summary = f"Top 10 regions by EV sales in {year}:\n"
    for _, row in result.iterrows():
        summary += f"  • {row['Region / Country']}: {row['EV Sales (vehicles)']:,} vehicles\n"

    return {"summary": summary, "dataframe": result, "year": year, "chart_type": "auto"}


def query_ev_sales_trend(question: str) -> dict:
    df = _select_sales_df(question)
    region = _extract_region(question)

    if "category" in df.columns and "parameter" in df.columns:
        filtered = df[
            (df['parameter'] == 'EV sales') &
            (df['category'] == 'Historical')
        ]
    else:
        filtered = df
    if region:
        filtered = filtered[
            filtered['region_country'].str.contains(region, case=False, na=False)
        ]

    result = (
        filtered
        .groupby(['year', 'region_country'])['value']
        .sum()
        .reset_index()
    )
    result.columns = ['Year', 'Region', 'EV Sales']

    label = region or "Global"
    total_growth = result.groupby('Year')['EV Sales'].sum()
    if len(total_growth) >= 2:
        start = total_growth.iloc[0]
        end   = total_growth.iloc[-1]
        growth_pct = ((end - start) / start * 100) if start > 0 else 0
        summary = (
            f"EV sales trend for {label}:\n"
            f"  • {int(total_growth.index[0])}: {int(start):,} vehicles\n"
            f"  • {int(total_growth.index[-1])}: {int(end):,} vehicles\n"
            f"  • Total growth: {growth_pct:.0f}%\n"
        )
    else:
        summary = f"EV sales trend data for {label}."

    return {"summary": summary, "dataframe": result, "chart_type": "auto"}


def query_ev_stock(question: str) -> dict:
    df = _select_sales_df(question)
    region = _extract_region(question)

    if "category" in df.columns and "parameter" in df.columns:
        filtered = df[
            (df['parameter'] == 'EV stock') &
            (df['category'] == 'Historical')
        ]
    else:
        filtered = df

    if region:
        filtered = filtered[
            filtered['region_country'].str.contains(region, case=False, na=False)
        ]

    result = (
        filtered
        .groupby(['year', 'region_country'])['value']
        .sum()
        .reset_index()
    )
    result.columns = ['Year', 'Region', 'EV Stock']

    label = region or "Global"
    latest_year = int(result['Year'].max()) if not result.empty else None
    latest_val = (
        result[result['Year'] == latest_year]['EV Stock'].sum()
        if latest_year is not None else 0
    )
    summary = (
        f"EV stock trend for {label}:\n"
        f"  • Latest year ({latest_year}): {int(latest_val):,} vehicles\n"
    ) if latest_year else f"EV stock trend data for {label}."

    return {"summary": summary, "dataframe": result, "chart_type": "auto"}


def query_bev_phev_compare(question: str) -> dict:
    df = _load_ev()
    year = _extract_year(question)

    filtered = df[
        (df['parameter'] == 'EV sales') &
        (df['category'] == 'Historical') &
        (df['powertrain'].isin(['BEV', 'PHEV']))
    ]
    if year:
        filtered = filtered[filtered['year'] == year]

    result = (
        filtered
        .groupby(['year', 'powertrain'])['value']
        .sum()
        .reset_index()
    )
    result.columns = ['Year', 'Powertrain', 'Sales']

    bev_total  = result[result['Powertrain'] == 'BEV']['Sales'].sum()
    phev_total = result[result['Powertrain'] == 'PHEV']['Sales'].sum()
    total      = bev_total + phev_total
    bev_share  = (bev_total / total * 100) if total > 0 else 0

    summary = (
        f"BEV vs PHEV comparison:\n"
        f"  • BEV total: {int(bev_total):,} vehicles ({bev_share:.0f}% share)\n"
        f"  • PHEV total: {int(phev_total):,} vehicles ({100-bev_share:.0f}% share)\n"
        f"  • BEVs outsell PHEVs by {int(bev_total - phev_total):,} vehicles\n"
    )

    return {"summary": summary, "dataframe": result, "chart_type": "auto"}


def query_av_incidents(question: str) -> dict:
    df = _load_av()
    if df.empty:
        return {"summary": "AV incident data not available.", "dataframe": pd.DataFrame()}

    by_system = df['system_type'].value_counts().reset_index()
    by_system.columns = ['System Type', 'Incidents']

    engaged_col = 'Automation System Engaged?'
    engaged = df[df[engaged_col] == 'Yes'].shape[0] if engaged_col in df.columns else 0

    summary = (
        f"AV incident summary from NHTSA SGO reports:\n"
        f"  • Total incidents: {len(df):,}\n"
        f"  • ADAS incidents: {by_system[by_system['System Type']=='ADAS']['Incidents'].values[0] if 'ADAS' in by_system['System Type'].values else 0:,}\n"
        f"  • ADS incidents: {by_system[by_system['System Type']=='ADS']['Incidents'].values[0] if 'ADS' in by_system['System Type'].values else 0:,}\n"
        f"  • Incidents with automation engaged: {engaged:,}\n"
    )

    return {"summary": summary, "dataframe": by_system, "chart_type": "auto"}


def query_av_trend(question: str) -> dict:
    df = _load_av()
    if df.empty:
        return {"summary": "AV incident data not available.", "dataframe": pd.DataFrame()}

    if 'Report Year' not in df.columns or 'Report Month' not in df.columns:
        return {"summary": "AV incident trend data not available.", "dataframe": pd.DataFrame()}

    df['Report Year'] = pd.to_numeric(df['Report Year'], errors='coerce')
    df['Report Month'] = pd.to_numeric(df['Report Month'], errors='coerce')
    filtered = df.dropna(subset=['Report Year', 'Report Month'])
    trend = (
        filtered
        .groupby(['Report Year', 'Report Month', 'system_type'])
        .size()
        .reset_index(name='Incidents')
    )
    trend['Date'] = pd.to_datetime(
        trend[['Report Year', 'Report Month']]
        .rename(columns={'Report Year': 'year', 'Report Month': 'month'})
        .assign(day=1)
    )

    summary = (
        "AV incident trend over time (monthly):\n"
        f"  • Records: {len(trend):,}\n"
    )

    return {"summary": summary, "dataframe": trend[['Date', 'system_type', 'Incidents']], "chart_type": "auto"}


def query_av_severity(question: str) -> dict:
    df = _load_av()
    col = 'Highest Injury Severity Alleged'
    if df.empty or col not in df.columns:
        return {"summary": "Severity data not available.", "dataframe": pd.DataFrame()}

    result = df[col].value_counts().reset_index()
    result.columns = ['Severity', 'Count']

    summary = "AV incident injury severity breakdown:\n"
    for _, row in result.iterrows():
        summary += f"  • {row['Severity']}: {row['Count']:,} incidents\n"

    return {"summary": summary, "dataframe": result, "chart_type": "auto"}


def query_av_weather(question: str) -> dict:
    df = _load_av()
    if df.empty:
        return {"summary": "Weather data not available.", "dataframe": pd.DataFrame()}

    weather_cols = [c for c in df.columns
                    if c.startswith('Weather -')
                    and 'Unknown' not in c
                    and 'Other' not in c]
    counts = {}
    for wc in weather_cols:
        label = wc.replace('Weather - ', '')
        n = df[df[wc].astype(str).str.upper().isin(['YES', '1', 'TRUE'])].shape[0]
        if n > 0:
            counts[label] = n

    result = pd.DataFrame(list(counts.items()), columns=['Weather Condition', 'Incidents'])
    result = result.sort_values('Incidents', ascending=False)

    summary = "AV incidents by weather condition:\n"
    for _, row in result.iterrows():
        summary += f"  • {row['Weather Condition']}: {row['Incidents']:,} incidents\n"

    return {"summary": summary, "dataframe": result, "chart_type": "auto"}


# ── Main entry point ───────────────────────────────────────────────

INTENT_HANDLERS = {
    DataIntent.EV_SALES_RANKING: query_ev_sales_ranking,
    DataIntent.EV_SALES_TREND:   query_ev_sales_trend,
    DataIntent.EV_STOCK:         query_ev_stock,
    DataIntent.BEV_PHEV_COMPARE: query_bev_phev_compare,
    DataIntent.AV_INCIDENTS:     query_av_incidents,
    DataIntent.AV_SEVERITY:      query_av_severity,
    DataIntent.AV_WEATHER:       query_av_weather,
    DataIntent.AV_TREND:         query_av_trend,
}


def run_data_query(question: str) -> dict | None:
    """
    Main entry point. Returns a dict with:
      - summary: str  (text findings for the LLM to use as context)
      - dataframe: pd.DataFrame  (for chart rendering)
      - chart_type: str  (bar | line | pie)
    Returns None if the question is not data-oriented.
    """
    intent = classify_data_intent(question)
    if intent == DataIntent.NONE:
        return None
    handler = INTENT_HANDLERS.get(intent)
    if not handler:
        return None
    try:
        result = handler(question)
        if result and result.get("dataframe") is not None:
            df = result["dataframe"]
            if result.get("chart_type") in (None, "", "auto"):
                result["chart_type"] = _infer_chart_type(df)
        return result
    except Exception as e:
        return {"summary": f"Data query failed: {e}", "dataframe": pd.DataFrame()}


def _infer_chart_type(df: pd.DataFrame) -> str:
    """
    Infer a reasonable chart type from the dataframe shape and dtypes.
    Returns: "line" | "bar" | "pie" | "none"
    """
    if df is None or df.empty or len(df.columns) < 2:
        return "none"

    cols = df.columns.tolist()
    col0 = df[cols[0]]
    col1 = df[cols[1]]

    # Prefer line if a time-like column exists
    for c in cols:
        if "year" in str(c).lower() or "date" in str(c).lower():
            if is_datetime64_any_dtype(df[c]) or is_numeric_dtype(df[c]):
                return "line"

    # If first column is categorical, decide between pie and bar
    if col0.dtype == "object":
        unique_count = col0.nunique(dropna=True)
        if unique_count <= 6:
            return "pie"
        return "bar"

    # Default to bar for numeric pairs
    if is_numeric_dtype(col0) and is_numeric_dtype(col1):
        return "line"

    return "bar"
