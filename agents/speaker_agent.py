# """
# agents/speaker_agent.py
# Domain-aware: speakers (conference), artists (music), athletes/performers (sports).
# Augmented with ChromaDB RAG semantic search for richer historical context.
# """
import json
from tools.data_loader import filter_events, get_speaker_frequency, get_domain
from tools.ranker import rank_speakers
from tools.llm import call_llm

DOMAIN_LABELS = {
    "conference": {
        "entity":  "conference",
        "talent":  "speakers",
        "output":  "agenda topics + speaker mapping",
    },
    "music": {
        "entity":  "music festival",
        "talent":  "artists/performers",
        "output":  "stage lineup + set schedule",
    },
    "sports": {
        "entity":  "sporting event",
        "talent":  "athletes/teams/commentators",
        "output":  "match schedule + broadcast talent lineup",
    },
}


def _rag_context(category: str, geography: str, rag_ready: bool) -> tuple[list, bool]:
    """Return (rag_results, rag_used).  Silently degrades if ChromaDB unavailable."""
    if not rag_ready:
        return [], False
    try:
        from tools.embeddings import semantic_search
        query = f"{category} {geography} event speakers artists performers keynote"
        results = semantic_search(query, n_results=6)
        return results, True
    except Exception as e:
        print(f"[SpeakerAgent] RAG search failed: {e}")
        return [], False


def run(all_events, category, geography, audience_size,
        event_name="New Event", num_speakers=10, memory=None, rag_ready=False):

    domain    = get_domain(category)
    labels    = DOMAIN_LABELS.get(domain, DOMAIN_LABELS["conference"])
    freq_data = get_speaker_frequency(all_events, category, geography)
    ranked    = rank_speakers(freq_data, category, geography)
    top_ranked = ranked[:20]

    relevant = filter_events(all_events, category=category, geography=geography)
    if not relevant:
        relevant = filter_events(all_events, domain=domain)

    # ── RAG semantic search ───────────────────────────────────────────────────
    rag_results, rag_used = _rag_context(category, geography, rag_ready)
    rag_section = ""
    if rag_results:
        rag_section = (
            "\n\nSemantic search (RAG) over the vector store returned these additional "
            "similar past events — use them to refine talent recommendations:\n"
            + json.dumps(rag_results, indent=2)
        )

    context = {
        "event_name":         event_name,
        "event_type":         labels["entity"],
        "category":           category,
        "geography":          geography,
        "audience_size":      audience_size,
        "num_talent_needed":  num_speakers,
        "dataset_ranked_talent": [
            {
                "name":            s["name"],
                "appearances":     s["frequency"],
                "relevance_score": s["relevance_score"],
            }
            for s in top_ranked
        ],
        "similar_events":           [str(e.get("Event Name", "")) for e in relevant[:10]],
        "total_events_analyzed":    len(relevant),
    }

    prompt = f"""You are a {labels['entity']} programming director.

The following {labels['talent']} were ranked by a weighted algorithm from {len(relevant)} real past events.
Your job is to build the {labels['output']}.
{rag_section}

Context:
{json.dumps(context, indent=2)}

Tasks:
1. Recommend {num_speakers} {labels['talent']} — mix from ranked list + new suggestions.
2. For each: name, expertise/genre/sport, why they fit, suggested slot/talk title, type.
3. Build a draft {labels['output']}.
4. Suggest 3 headline themes or marquee acts.

Respond ONLY in JSON:
{{
  "recommended_speakers": [
    {{"name": "...", "expertise": "...", "reason": "...", "suggested_talk_title": "...", "type": "keynote/panel/workshop/headliner/opener/athlete"}}
  ],
  "agenda_outline": [
    {{"time": "9:00 AM", "session": "...", "speaker": "...", "duration_mins": 45}}
  ],
  "keynote_themes": ["theme 1", "theme 2", "theme 3"],
  "historical_insight": "One sentence about talent patterns from historical data"
}}"""

    raw = call_llm(prompt)
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(raw)
    except Exception:
        result = {"raw_response": raw}

    result["dataset_ranked_speakers"] = top_ranked
    result["historical_events_used"]  = len(relevant)
    result["domain"]                  = domain
    result["rag_used"]                = rag_used
    return result
