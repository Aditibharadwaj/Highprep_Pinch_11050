"""
tools/ranker.py
Weighted multi-factor ranking for sponsors, speakers, venues, exhibitors.
Domain-aware: conference / music / sports.
"""

SPONSOR_WEIGHTS = {
    "industry_relevance": 0.35,
    "geo_frequency":      0.25,
    "historical_frequency": 0.20,
    "audience_overlap":   0.20,
}

def rank_sponsors(candidates, category, geography):
    max_freq = max((c.get("frequency",0) for c in candidates), default=1)
    for c in candidates:
        c["relevance_score"] = round(100 * (
            SPONSOR_WEIGHTS["industry_relevance"]   * _keyword_match(c.get("name",""), category) +
            SPONSOR_WEIGHTS["geo_frequency"]        * 1.0 +
            SPONSOR_WEIGHTS["historical_frequency"] * c.get("frequency",0) / max(max_freq,1) +
            SPONSOR_WEIGHTS["audience_overlap"]     * 0.7
        ))
        c["tier"] = _sponsor_tier(c["relevance_score"])
    return sorted(candidates, key=lambda x: -x["relevance_score"])


def _sponsor_tier(score):
    if score >= 80: return "Platinum"
    if score >= 65: return "Gold"
    if score >= 50: return "Silver"
    return "Bronze"


SPEAKER_WEIGHTS = {
    "topic_relevance":     0.30,
    "speaking_experience": 0.25,
    "influence":           0.25,
    "geo_preference":      0.20,
}

def rank_speakers(candidates, category, geography):
    """Works for speakers, artists, athletes — same scoring logic."""
    max_app = max((c.get("frequency",0) for c in candidates), default=1)
    for c in candidates:
        c["relevance_score"] = round(100 * (
            SPEAKER_WEIGHTS["topic_relevance"]      * _keyword_match(c.get("name",""), category) +
            SPEAKER_WEIGHTS["speaking_experience"]  * c.get("frequency",0) / max(max_app,1) +
            SPEAKER_WEIGHTS["influence"]            * 0.6 +
            SPEAKER_WEIGHTS["geo_preference"]       * 1.0
        ))
    return sorted(candidates, key=lambda x: -x["relevance_score"])


# ── Domain-aware exhibitor clustering ────────────────────────────────────────

CONF_CLUSTERS = {
    "Enterprise":   ["ibm","microsoft","oracle","sap","accenture","deloitte","pwc","kpmg",
                     "infosys","wipro","tcs","cognizant","aws","google","salesforce",
                     "cisco","capgemini","atos","hcl"],
    "Tools/Platform": ["platform","sdk","api","tools","cloud","hub","chain","data",
                       "analytics","langchain","databricks","hugging"],
    "Research":     ["university","institute","research","foundation","lab","mila",
                     "deepmind","openai","stanford","mit","uc"],
    "Startup":      [],
}

MUSIC_CLUSTERS = {
    "Beverage/Lifestyle": ["kingfisher","budweiser","heineken","red bull","jagermeister",
                           "bacardi","monster","pernod","tiger beer","anheuser"],
    "Media/Streaming":    ["vh1","spotify","jiostar","star","amazon music","apple music",
                           "youtube music","mtv"],
    "Telecom/Tech":       ["oneplus","t-mobile","jio","airtel","samsung","apple"],
    "Brand Activations":  ["zomato","swiggy","klook","grab","amex","h&m","puma"],
    "Stage/Equipment":    ["jbl","bose","pioneer","serato","roland"],
}

SPORTS_CLUSTERS = {
    "Title Sponsors":     ["tata","dream11","aramco","oracle","hp","petronas"],
    "Official Partners":  ["ceat","mrf","angone","rupay","rolex","dhl","pirelli",
                           "heineken","aws","salesforce","nissan"],
    "Broadcast/Media":    ["jiostar","star sports","sky sports","espn","sony liv",
                           "willow","bcci","icc","formula 1"],
    "Lifestyle/Luxury":   ["rolex","louis vuitton","hugo boss","tommy hilfiger",
                           "marina bay sands","mgm","wynn"],
    "Merchandise/Retail": ["merchandise","food stalls","fan zones","craft beer"],
}

def cluster_exhibitors(exhibitors, domain="conference"):
    cluster_map = {
        "music":      MUSIC_CLUSTERS,
        "sports":     SPORTS_CLUSTERS,
        "conference": CONF_CLUSTERS,
    }.get(domain, CONF_CLUSTERS)

    for ex in exhibitors:
        ex["cluster"] = _assign_cluster(ex.get("name","").lower(), cluster_map)
    return exhibitors


def _assign_cluster(name, cluster_map):
    for cluster, keywords in cluster_map.items():
        if any(kw in name for kw in keywords):
            return cluster
    # Default per domain
    first_key = list(cluster_map.keys())
    return first_key[-1] if first_key else "Other"


def rank_venues(candidates, expected_attendance, budget_level):
    budget_mult = {"low": 0.6, "medium": 1.0, "high": 1.5}.get(budget_level, 1.0)
    for v in candidates:
        capacity    = v.get("capacity",0) or 0
        past_events = v.get("past_tech_events",0) or 0
        cap_score   = min(capacity/max(expected_attendance,1),1.0) if capacity >= expected_attendance*0.8 else 0.4
        v["relevance_score"] = round(100*(0.40*cap_score + 0.35*budget_mult*0.6 + 0.25*min(past_events/10.0,1.0)))
    return sorted(candidates, key=lambda x: -x["relevance_score"])


def _keyword_match(text, query):
    tw = set(text.lower().split())
    qw = set(query.lower().split())
    if not qw: return 0.5
    return len(tw & qw) / len(qw)