"""
Classifies incoming questions to route retrieval strategy.

Categories:
  - technical   → deep AV/EV engineering docs
  - regulatory  → standards, legislation, policy docs
  - market      → EV adoption stats, IEA data, forecasts
  - general     → broad questions, use full corpus
"""
from enum import Enum


class QueryCategory(str, Enum):
    TECHNICAL   = "technical"
    REGULATORY  = "regulatory"
    MARKET      = "market"
    GENERAL     = "general"


_TECHNICAL_KEYWORDS = [
    "lidar", "radar", "sensor", "fusion", "bms", "battery", "soc", "soh",
    "powertrain", "inverter", "adas", "v2x", "can bus", "iso 26262",
    "functional safety", "charging", "ccs", "nacs", "chademo", "v2g",
    "solid state", "nmc", "lfp", "motor", "torque", "range", "efficiency",
]

_REGULATORY_KEYWORDS = [
    "regulation", "policy", "legislation", "standard", "sae j3016",
    "unece", "nhtsa", "directive", "mandate", "compliance", "approval",
    "type approval", "zev", "euro 7", "law", "rule", "framework",
]

_MARKET_KEYWORDS = [
    "market", "adoption", "sales", "forecast", "iea", "growth", "trend",
    "investment", "share", "penetration", "revenue", "cost", "subsidy",
    "incentive", "bloomberg", "statistics",
]


def classify_query(question: str) -> QueryCategory:
    """Return the category that best matches the question."""
    q = question.lower()

    scores = {
        QueryCategory.TECHNICAL:   sum(1 for kw in _TECHNICAL_KEYWORDS   if kw in q),
        QueryCategory.REGULATORY:  sum(1 for kw in _REGULATORY_KEYWORDS  if kw in q),
        QueryCategory.MARKET:      sum(1 for kw in _MARKET_KEYWORDS       if kw in q),
    }

    best_score = max(scores.values())
    if best_score == 0:
        return QueryCategory.GENERAL

    return max(scores, key=scores.get)
