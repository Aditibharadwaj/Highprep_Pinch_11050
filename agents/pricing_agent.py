"""
agents/pricing_agent.py
Domain-aware pricing + attendance prediction using real dataset stats.
"""
import json
import numpy as np
from tools.data_loader import filter_events, get_pricing_stats, get_domain
from tools.llm import call_llm

DOMAIN_LABELS = {
    "conference": {"tiers": ["Early Bird","Standard","VIP"],         "entity": "conference"},
    "music":      {"tiers": ["General Admission","Floor/Pit","VIP"], "entity": "music festival"},
    "sports":     {"tiers": ["Standard","Premium","Hospitality"],    "entity": "sporting event"},
}

def _predict_attendance(stats, target_audience, num_sponsors=5):
    base = stats["actual_attendance"]["mean"] or target_audience * 0.75
    predicted = int(base * (1 + 0.03 * min(num_sponsors, 15)))
    return {
        "conservative": int(predicted * 0.80),
        "base_case":    predicted,
        "optimistic":   int(predicted * 1.20),
    }

def _revenue_scenarios(attendance, pricing, sp_mean):
    scenarios = {}
    for scenario, att in attendance.items():
        eb_rev  = int(att * 0.35 * pricing.get("early_bird", 0))
        std_rev = int(att * 0.50 * pricing.get("standard",   0))
        vip_rev = int(att * 0.15 * pricing.get("vip",        0))
        ticket_rev = eb_rev + std_rev + vip_rev
        total      = ticket_rev + int(sp_mean)
        scenarios[scenario] = {
            "ticket_revenue": ticket_rev,
            "total_revenue":  total,
            "profit":         total - 80_000,
        }
    return scenarios

def run(all_events, category, geography, target_audience, budget="medium",
        event_name="New Event", num_sponsors=5, memory=None):
    domain    = get_domain(category)
    labels    = DOMAIN_LABELS.get(domain, DOMAIN_LABELS["conference"])
    stats     = get_pricing_stats(all_events, category, geography)
    att_pred  = _predict_attendance(stats, target_audience, num_sponsors)
    dataset_prices = {
        "early_bird": stats["early_bird"]["mean"],
        "standard":   stats["standard"]["mean"],
        "vip":        stats["vip"]["mean"],
        "sponsorship_mean": stats["sponsorship_revenue"]["mean"],
    }
    rev_scenarios  = _revenue_scenarios(att_pred, dataset_prices, stats["sponsorship_revenue"]["mean"])
    breakeven      = int(80_000 / max(dataset_prices["standard"], 1))

    context = {
        "event_name":     event_name,
        "event_type":     labels["entity"],
        "category":       category,
        "geography":      geography,
        "target_audience": target_audience,
        "budget_level":   budget,
        "ticket_tier_names": labels["tiers"],
        "dataset_pricing_stats":          stats,
        "dataset_attendance_prediction":  att_pred,
        "dataset_revenue_scenarios":      rev_scenarios,
        "dataset_breakeven_tickets":      breakeven,
        "events_analyzed":                stats["sample_size"],
    }

    prompt = f"""You are a data-driven {labels['entity']} pricing strategist.

Pricing stats computed from {stats['sample_size']} real historical events.
Tier names for this {labels['entity']}: {labels['tiers']}.

Context:
{json.dumps(context, indent=2)}

Tasks:
1. Confirm or refine 3 ticket tiers using the dataset stats as ground truth.
2. Validate the attendance predictions and revenue scenarios.
3. Explain the price-attendance relationship.
4. Suggest when to open the first tier (weeks before event).

Respond ONLY in JSON:
{{
  "recommended_pricing": {{
    "early_bird": {{"price": 0, "discount_pct": 0, "open_weeks_before": 0}},
    "standard":   {{"price": 0}},
    "vip":        {{"price": 0, "includes": ["..."]}}
  }},
  "attendance_prediction": {{"conservative": 0, "base_case": 0, "optimistic": 0}},
  "revenue_scenarios": {{
    "conservative": {{"ticket_revenue": 0, "total_revenue": 0, "profit": 0}},
    "base_case":    {{"ticket_revenue": 0, "total_revenue": 0, "profit": 0}},
    "optimistic":   {{"ticket_revenue": 0, "total_revenue": 0, "profit": 0}}
  }},
  "break_even_tickets": 0,
  "pricing_rationale": "...",
  "conversion_rate_assumptions": {{
    "early_bird_conversion": "35%",
    "standard_conversion": "50%",
    "vip_conversion": "15%"
  }}
}}"""

    raw = call_llm(prompt)
    raw = raw.replace("```json","").replace("```","").strip()
    try:
        result = json.loads(raw)
    except:
        result = {"raw_response": raw}

    result["dataset_stats"]                  = stats
    result["dataset_attendance_prediction"]  = att_pred
    result["dataset_revenue_scenarios"]      = rev_scenarios
    result["dataset_breakeven_tickets"]      = breakeven
    result["events_analyzed"]                = stats["sample_size"]
    result["domain"]                         = domain
    return result