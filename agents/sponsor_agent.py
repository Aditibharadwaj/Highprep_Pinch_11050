"""
agents/sponsor_agent.py
Domain-aware sponsor recommendations: conference, music festival, sports event.
Augmented with ChromaDB RAG semantic search for richer historical context.
"""
import json
from tools.data_loader import filter_events, get_sponsor_frequency, get_domain
from tools.ranker import rank_sponsors
from tools.llm import call_llm

# Domain-specific LLM terminology
DOMAIN_LABELS = {
    "conference": {
        "entity":  "conference",
        "sponsors": "sponsors",
        "value":   "professional audience, brand visibility, lead generation",
    },
    "music": {
        "entity":  "music festival",
        "sponsors": "brand partners & activations",
        "value":   "mass reach, lifestyle brand alignment, experiential marketing",
    },
    "sports": {
        "entity":  "sporting event",
        "sponsors": "official partners & title sponsors",
        "value":   "massive viewership, jersey/ground branding, broadcast exposure",
    },
}


def _rag_context(category: str, geography: str, rag_ready: bool) -> tuple[list, bool]:
    """Return (rag_results, rag_used).  Silently degrades if ChromaDB unavailable."""
    if not rag_ready:
        return [], False
    try:
        from tools.embeddings import semantic_search
        query = f"{category} {geography} event sponsors brand partners"
        results = semantic_search(query, n_results=6)
        return results, True
    except Exception as e:
        print(f"[SponsorAgent] RAG search failed: {e}")
        return [], False


def run(all_events, category, geography, audience_size,
        event_name="New Event", memory=None, rag_ready=False):

    domain    = get_domain(category)
    labels    = DOMAIN_LABELS.get(domain, DOMAIN_LABELS["conference"])
    freq_data = get_sponsor_frequency(all_events, category, geography)
    ranked    = rank_sponsors(freq_data, category, geography)
    top_ranked = ranked[:15]

    relevant_count = len(filter_events(all_events, category=category, geography=geography))
    if not relevant_count:
        relevant_count = len(filter_events(all_events, domain=domain))

    # ── RAG semantic search ───────────────────────────────────────────────────
    rag_results, rag_used = _rag_context(category, geography, rag_ready)
    rag_section = ""
    if rag_results:
        rag_section = (
            "\n\nSemantic search (RAG) over the vector store returned these additional "
            "similar past events — use them to refine sponsor recommendations:\n"
            + json.dumps(rag_results, indent=2)
        )

    context = {
        "event_name":       event_name,
        "event_type":       labels["entity"],
        "category":         category,
        "geography":        geography,
        "audience_size":    audience_size,
        "sponsor_value_prop": labels["value"],
        "dataset_ranked_sponsors": [
            {
                "name":                  s["name"],
                "historical_appearances": s["frequency"],
                "relevance_score":        s["relevance_score"],
                "suggested_tier":         s["tier"],
            }
            for s in top_ranked
        ],
        "total_events_analyzed": relevant_count,
    }

    prompt = f"""You are a senior {labels['entity']} sponsorship strategist.

The following {labels['sponsors']} were ranked by a weighted algorithm (industry relevance 35%,
geo frequency 25%, historical frequency 20%, audience overlap 20%) from {relevant_count} real past events.
{rag_section}

Context:
{json.dumps(context, indent=2)}

Tasks:
1. Confirm the top 8 {labels['sponsors']} from the ranked list with specific reasons.
2. Suggest 3 NEW {labels['sponsors']} not in the list who logically fit this {labels['entity']}.
3. Write a customised proposal outline (4 bullet points) tailored to a {labels['entity']}.
4. Write one outreach email template for the top {labels['sponsors'].split()[0]}.

Respond ONLY in JSON:
{{
  "recommended_sponsors": [
    {{"name": "...", "reason": "...", "tier": "Platinum/Gold/Silver/Bronze", "priority_score": 1-10}}
  ],
  "additional_suggestions": [
    {{"name": "...", "reason": "..."}}
  ],
  "proposal_outline": ["bullet 1", "bullet 2", "bullet 3", "bullet 4"],
  "outreach_email_template": "Dear [Name], ..."
}}"""

    raw = call_llm(prompt)
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(raw)
    except Exception:
        result = {"raw_response": raw}

    result["dataset_ranked_sponsors"] = top_ranked
    result["historical_events_used"]  = relevant_count
    result["domain"]                  = domain
    result["rag_used"]                = rag_used
    return result