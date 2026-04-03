"""
Lightweight spec comparison extractor for vehicle documents.
Extracts common EV specs from retrieved context chunks and formats
a side-by-side table. Designed to be resilient to messy PDF text.
"""
from __future__ import annotations
import os
import re


FIELDS = [
    "Battery (kWh)",
    "Range",
    "Power",
    "Torque",
    "0-100 km/h",
    "Top speed",
    "Charging (AC)",
    "Charging (DC)",
    "Drive",
    "Seating",
    "Weight",
    "Dimensions",
]


def build_spec_table(question: str, chunks: list[dict]) -> str:
    vehicles = _detect_vehicles(question, chunks)
    if not vehicles:
        return ""

    per_vehicle = {v: _extract_specs_for_vehicle(v, chunks) for v in vehicles}

    # Markdown table
    headers = ["Spec"] + vehicles
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for field in FIELDS:
        row = [field]
        for v in vehicles:
            row.append(per_vehicle[v].get(field, "Not stated in sources"))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _detect_vehicles(question: str, chunks: list[dict]) -> list[str]:
    q = question.lower()
    vehicles: list[str] = []

    # Try to parse "X vs Y" or "X versus Y"
    for splitter in [" vs ", " versus ", " compare ", " comparison "]:
        if splitter in q:
            parts = [p.strip(" ,") for p in q.split(splitter) if p.strip()]
            # keep original casing from question by slicing
            if len(parts) >= 2:
                vehicles = [_titleize(p) for p in parts[:2]]
                break

    # Fallback to source filenames
    if not vehicles:
        sources = []
        for c in chunks:
            s = str(c.get("source", "")).strip()
            if s:
                sources.append(s)
        sources = list(dict.fromkeys(sources))
        for s in sources:
            vehicles.append(_name_from_source(s))

    # Deduplicate and keep order
    seen = set()
    out = []
    for v in vehicles:
        key = v.lower()
        if key not in seen and v:
            seen.add(key)
            out.append(v)
    return out


def _extract_specs_for_vehicle(vehicle: str, chunks: list[dict]) -> dict:
    specs: dict = {}
    relevant = _filter_chunks_for_vehicle(vehicle, chunks)
    text = "\n".join([c.get("content", "") for c in relevant])
    if not text:
        text = "\n".join([c.get("content", "") for c in chunks])

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    joined = " ".join(lines)

    specs["Battery (kWh)"] = _first_match(joined, [
        r"(\d{2,3}\.?\d*)\s*kwh",
        r"battery\s*(?:capacity)?\s*[:\-]?\s*(\d{2,3}\.?\d*)\s*kwh",
    ])
    specs["Range"] = _first_match(joined, [
        r"range\s*[:\-]?\s*(\d{2,4})\s*(km|mi)",
        r"(\d{2,4})\s*(km|mi)\s*range",
    ], keep_units=True)
    specs["Power"] = _first_match(joined, [
        r"(\d{2,4})\s*(kw|hp)\b",
        r"power\s*[:\-]?\s*(\d{2,4})\s*(kw|hp)\b",
    ], keep_units=True)
    specs["Torque"] = _first_match(joined, [
        r"(\d{2,4})\s*nm\b",
        r"torque\s*[:\-]?\s*(\d{2,4})\s*nm\b",
    ], keep_units=True)
    specs["0-100 km/h"] = _first_match(joined, [
        r"0\s*[-–]\s*100\s*km\/h\s*[:\-]?\s*(\d+\.?\d*)\s*s",
        r"0\s*[-–]\s*60\s*mph\s*[:\-]?\s*(\d+\.?\d*)\s*s",
    ], keep_units=True, unit_override="s")
    specs["Top speed"] = _first_match(joined, [
        r"top\s*speed\s*[:\-]?\s*(\d{2,3})\s*(km\/h|mph)",
    ], keep_units=True)
    specs["Charging (AC)"] = _first_match(joined, [
        r"ac\s*charging\s*[:\-]?\s*(\d{1,3}\.?\d*)\s*kw",
        r"(\d{1,3}\.?\d*)\s*kw\s*ac",
    ], keep_units=True, unit_override="kW")
    specs["Charging (DC)"] = _first_match(joined, [
        r"dc\s*charging\s*[:\-]?\s*(\d{1,3}\.?\d*)\s*kw",
        r"fast\s*charging\s*[:\-]?\s*(\d{1,3}\.?\d*)\s*kw",
        r"(\d{1,3}\.?\d*)\s*kw\s*dc",
    ], keep_units=True, unit_override="kW")
    specs["Drive"] = _first_match(joined, [
        r"\b(awd|fwd|rwd)\b",
        r"(all-wheel drive|front-wheel drive|rear-wheel drive)",
    ])
    specs["Seating"] = _first_match(joined, [
        r"seating\s*[:\-]?\s*(\d)\s*(seats|seat)",
        r"(\d)\s*(seats|seat)",
    ], keep_units=True)
    specs["Weight"] = _first_match(joined, [
        r"(?:kerb|curb|gross)?\s*weight\s*[:\-]?\s*(\d{3,4})\s*kg",
        r"(\d{3,4})\s*kg",
    ], keep_units=True)
    specs["Dimensions"] = _first_match(joined, [
        r"(\d{3,4})\s*x\s*(\d{3,4})\s*x\s*(\d{3,4})\s*mm",
        r"length\s*[:\-]?\s*(\d{3,4})\s*mm.*width\s*[:\-]?\s*(\d{3,4})\s*mm.*height\s*[:\-]?\s*(\d{3,4})\s*mm",
    ], keep_units=True)

    # Clean empty
    return {k: v for k, v in specs.items() if v}


def _filter_chunks_for_vehicle(vehicle: str, chunks: list[dict]) -> list[dict]:
    v = vehicle.lower()
    out = []
    for c in chunks:
        src = str(c.get("source", "")).lower()
        content = str(c.get("content", "")).lower()
        if v in src or v in content:
            out.append(c)
    return out


def _first_match(text: str, patterns: list[str], keep_units: bool = False, unit_override: str | None = None) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if not m:
            continue
        if keep_units:
            if len(m.groups()) >= 2:
                val = f"{m.group(1)} {unit_override or m.group(2)}"
            else:
                val = f"{m.group(1)}{(' ' + unit_override) if unit_override else ''}"
        else:
            val = m.group(1) if m.groups() else m.group(0)
        return val.strip()
    return None


def _name_from_source(source: str) -> str:
    base = os.path.splitext(os.path.basename(source))[0]
    base = base.replace("_", " ").replace("-", " ")
    return _titleize(base)


def _titleize(text: str) -> str:
    return " ".join([t.capitalize() for t in re.split(r"\s+", text) if t])
