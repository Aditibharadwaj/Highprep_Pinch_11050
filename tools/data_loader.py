"""
tools/data_loader.py
Loads and normalizes the merged Excel dataset.
Now supports Conference, Music Festival, and Sports domains.
"""
import pandas as pd
import json
import os
import numpy as np

DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/events_merged_2025_2026.xlsx")

# ── Domain mappings ──────────────────────────────────────────────────────────
MUSIC_CATEGORIES    = {"EDM", "Pop/Rock", "Indie/Rock", "Rock/Alternative", "Rock/Pop",
                       "Multi-Genre", "Electronic/World", "Hip-Hop/R&B", "Music",
                       "Music Festival"}   # generic PS category
SPORTS_CATEGORIES   = {"Cricket", "Motorsports", "Football", "Basketball", "Tennis",
                       "Golf", "American Football", "Sports"}
CONF_CATEGORIES     = {"AI", "Web3", "ClimateTech", "Startup", "Startup/Tech", "AI/ML",
                       "Developer", "SaaS", "Tech"}

def get_domain(category: str) -> str:
    """Return 'music', 'sports', or 'conference' for a given category string."""
    cat = category.strip()
    if cat in MUSIC_CATEGORIES:   return "music"
    if cat in SPORTS_CATEGORIES:  return "sports"
    return "conference"


def load_events(path: str = DATA_PATH) -> list[dict]:
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Dataset not found at {path}.")
    df.columns  = [c.strip() for c in df.columns]
    df          = df.fillna("")
    events      = df.to_dict(orient="records")
    # Inject domain into each event
    for e in events:
        e["_domain"] = get_domain(str(e.get("Category", "")))
    return events


def filter_events(
    events:    list[dict],
    category:  str = "",
    geography: str = "",
    year:      int = None,
    domain:    str = "",          # "conference" | "music" | "sports" | ""
) -> list[dict]:
    result = events
    if domain:
        result = [e for e in result if e.get("_domain") == domain]
    if category:
        result = [e for e in result
                  if category.lower() in str(e.get("Category", "")).lower()]
    if geography:
        result = [e for e in result
                  if geography.lower() in str(e.get("Geography", "")).lower()]
    if year:
        result = [e for e in result if str(e.get("Year", "")) == str(year)]
    return result


def get_unique_values(events: list[dict], field: str) -> list[str]:
    values = set()
    for e in events:
        val = str(e.get(field, "")).strip()
        if val:
            for part in val.split(","):
                part = part.strip()
                if part:
                    values.add(part)
    return sorted(values)


def summarize_dataset(events: list[dict]) -> dict:
    conf  = [e for e in events if e.get("_domain") == "conference"]
    music = [e for e in events if e.get("_domain") == "music"]
    sports= [e for e in events if e.get("_domain") == "sports"]
    return {
        "total_events":  len(events),
        "conference":    len(conf),
        "music":         len(music),
        "sports":        len(sports),
        "years":         sorted(set(str(e.get("Year","")) for e in events if e.get("Year"))),
        "categories":    sorted(set(str(e.get("Category","")) for e in events if e.get("Category"))),
        "geographies":   sorted(set(str(e.get("Geography","")) for e in events if e.get("Geography"))),
    }


# ── Shared helpers (used by all agents) ──────────────────────────────────────

def _parse_float(val) -> float | None:
    try:
        return float(str(val).replace("$","").replace(",","").strip())
    except:
        return None

def _freq_list(events: list[dict], field: str) -> list[dict]:
    freq: dict[str, int] = {}
    for e in events:
        for item in str(e.get(field,"")).split(","):
            item = item.strip()
            if item and item.lower() not in ("","n/a","none","unknown","tbd"):
                freq[item] = freq.get(item, 0) + 1
    return [{"name": k, "frequency": v} for k, v in sorted(freq.items(), key=lambda x: -x[1])]


def get_sponsor_frequency(events, category, geography):
    relevant = filter_events(events, category=category, geography=geography)
    if not relevant:
        relevant = filter_events(events, domain=get_domain(category))
    return _freq_list(relevant, "Sponsors")


def get_speaker_frequency(events, category, geography):
    """Works for speakers (conf), artists (music), athletes (sports)."""
    relevant = filter_events(events, category=category, geography=geography)
    if not relevant:
        relevant = filter_events(events, domain=get_domain(category))
    return _freq_list(relevant, "Key Speakers")


def get_exhibitor_frequency(events, category, geography):
    relevant = filter_events(events, category=category, geography=geography)
    if not relevant:
        relevant = filter_events(events, domain=get_domain(category))
    return _freq_list(relevant, "Key Exhibitors")


def get_pricing_stats(events, category, geography):
    relevant = filter_events(events, category=category, geography=geography)
    if len(relevant) < 3:
        relevant = filter_events(events, domain=get_domain(category))
    if len(relevant) < 3:
        relevant = events

    def collect(field):
        return [v for e in relevant
                if (v := _parse_float(e.get(field))) and v > 0]

    def stats(arr):
        if not arr:
            return {"mean": 0, "median": 0, "min": 0, "max": 0, "count": 0}
        return {
            "mean":   round(float(np.mean(arr)), 2),
            "median": round(float(np.median(arr)), 2),
            "min":    round(float(np.min(arr)), 2),
            "max":    round(float(np.max(arr)), 2),
            "count":  len(arr),
        }

    sp_rev  = collect("Sponsorship Revenue")
    attend  = collect("Actual Attendance")
    return {
        "early_bird":          stats(collect("Ticket Price Early")),
        "standard":            stats(collect("Ticket Price Standard")),
        "vip":                 stats(collect("Ticket Price Vip")),
        "actual_attendance":   stats(attend),
        "audience_size":       stats(collect("Audience Size")),
        "sponsorship_revenue": stats(sp_rev),
        "avg_duration_days":   round(float(np.mean([e.get("Event Duration Days",2) for e in relevant if e.get("Event Duration Days")])) if relevant else 2, 1),
        "avg_num_speakers":    round(float(np.mean([e.get("Num Speakers",10)     for e in relevant if e.get("Num Speakers")])) if relevant else 10, 0),
        "avg_num_exhibitors":  round(float(np.mean([e.get("Num Exhibitors",20)   for e in relevant if e.get("Num Exhibitors")])) if relevant else 20, 0),
        "sample_size":         len(relevant),
        "domain":              get_domain(category),
    }


def get_venue_context(events, geography, city):
    relevant   = filter_events(events, geography=geography)
    city_events= [e for e in relevant if city.lower() in str(e.get("City","")).lower()]
    audiences  = [float(e.get("Audience Size",0)) for e in relevant if e.get("Audience Size")]
    return {
        "past_events_in_city":    len(city_events),
        "past_events_in_region":  len(relevant),
        "avg_audience_in_region": round(sum(audiences)/max(len(audiences),1), 0),
        "city_tier":              (lambda v: int(float(v)) if str(v).strip().replace('.','',1).isdigit() else 2)(city_events[0].get("City Tier", 2)) if city_events else 2,
    }


if __name__ == "__main__":
    events = load_events()
    print(json.dumps(summarize_dataset(events), indent=2))