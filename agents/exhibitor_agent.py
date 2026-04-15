"""
agents/exhibitor_agent.py
Domain-aware exhibitor/vendor clustering: conference / music / sports.
"""
import json
from tools.data_loader import filter_events, get_exhibitor_frequency, get_domain
from tools.ranker import cluster_exhibitors
from tools.llm import call_llm

DOMAIN_LABELS = {
    "conference": {"entity": "conference",     "vendor_type": "exhibitors",            "booth": "exhibitor booth"},
    "music":      {"entity": "music festival", "vendor_type": "brand activations & stalls", "booth": "activation zone"},
    "sports":     {"entity": "sporting event", "vendor_type": "official partner zones & merchandise", "booth": "partner zone"},
}

def run(all_events, category, geography, audience_size, budget="medium", event_name="New Event"):
    domain    = get_domain(category)
    labels    = DOMAIN_LABELS.get(domain, DOMAIN_LABELS["conference"])
    freq_data = get_exhibitor_frequency(all_events, category, geography)

    max_freq  = max((e["frequency"] for e in freq_data), default=1)
    for ex in freq_data:
        ex["relevance_score"] = round(100 * ex["frequency"] / max_freq)

    clustered      = cluster_exhibitors(freq_data, domain=domain)
    cluster_summary: dict[str, list] = {}
    for ex in clustered[:30]:
        cluster_summary.setdefault(ex["cluster"], []).append(
            {"name": ex["name"], "frequency": ex["frequency"], "score": ex["relevance_score"]}
        )

    relevant_count = len(filter_events(all_events, category=category, geography=geography)) or \
                     len(filter_events(all_events, domain=domain))

    context = {
        "event_name":       event_name,
        "event_type":       labels["entity"],
        "category":         category,
        "geography":        geography,
        "audience_size":    audience_size,
        "budget_level":     budget,
        "vendor_type":      labels["vendor_type"],
        "dataset_clustered": cluster_summary,
        "total_events_analyzed": relevant_count,
    }

    prompt = f"""You are a {labels['entity']} {labels['vendor_type']} manager.

The following {labels['vendor_type']} were clustered from a structured dataset of {relevant_count} real past events.

Context:
{json.dumps(context, indent=2)}

Tasks:
1. Confirm or refine the clusters from the dataset. Add up to 3 new logical additions per cluster.
2. Suggest {labels['booth']} pricing tiers (3 tiers).
3. Give a one-line pitch for each cluster.

Respond ONLY in JSON:
{{
  "exhibitor_clusters": {{
    "ClusterName": [{{"name": "...", "reason": "..."}}]
  }},
  "booth_pricing": {{
    "Tier 1": {{"price": "...", "includes": ["..."]}},
    "Tier 2": {{"price": "...", "includes": ["..."]}},
    "Tier 3": {{"price": "...", "includes": ["..."]}}
  }},
  "cluster_pitch": {{"ClusterName": "..."}},
  "total_exhibitor_revenue_estimate": "..."
}}"""

    raw = call_llm(prompt)
    raw = raw.replace("```json","").replace("```","").strip()
    try:
        result = json.loads(raw)
    except:
        result = {"raw_response": raw}

    result["dataset_clustered_exhibitors"] = cluster_summary
    result["historical_events_used"]       = relevant_count
    result["domain"]                       = domain
    return result