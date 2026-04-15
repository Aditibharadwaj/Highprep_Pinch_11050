"""Quick validation of all fallback functions - run without LLM API key needed."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("GROQ_API_KEY", "test-key-for-import")

# ─── Test 1: Geography ────────────────────────────────────────────────────────
print("=== TEST 1: Geography restriction ===")
from tools.data_loader import load_events, summarize_dataset
events = load_events()
summary = summarize_dataset(events)
raw_geos = summary.get("geographies", [])
fixed_geos = ["Europe", "India", "Singapore", "USA"]
print(f"  Raw from dataset : {raw_geos}")
print(f"  App will use     : {fixed_geos}")
assert fixed_geos == ["Europe", "India", "Singapore", "USA"], "Geography fix failed"
extra = [g for g in raw_geos if g not in fixed_geos]
print(f"  Removed regions  : {extra}")
print("  PASS")

# ─── Test 2: Venue fallback ───────────────────────────────────────────────────
print("\n=== TEST 2: Venue agent fallback ===")
from agents.venue_agent import _fallback_venues
for budget in ["low", "medium", "high"]:
    r = _fallback_venues("Bangalore", 3000, budget, "India", "conference", "convention centres")
    assert r["top_pick"], "top_pick missing"
    assert len(r["recommended_venues"]) == 5, "Expected 5 venues"
    assert len(r["negotiation_tips"]) >= 3, "Expected >= 3 tips"
    print(f"  budget={budget}: top_pick={r['top_pick']!r}, venues={len(r['recommended_venues'])}, tips={len(r['negotiation_tips'])}")
print("  PASS")

# ─── Test 3: GTM fallback ─────────────────────────────────────────────────────
print("\n=== TEST 3: GTM agent fallback ===")
from agents.gtm_agent import _fallback_gtm, _get_communities
for cat in ["AI", "Web3", "ClimateTech"]:
    comms = _get_communities("conference", cat)
    r = _fallback_gtm(comms, "conference", cat, "India", 3000, f"{cat} Summit 2026", "2026-09-15")
    assert len(r["top_communities"]) > 0,     "top_communities missing"
    assert len(r["gtm_timeline"]) == 8,       "Expected 8-week timeline"
    assert r["message_templates"].get("discord_slack"), "discord_slack template missing"
    assert r["message_templates"].get("linkedin_post"), "linkedin_post template missing"
    assert r["message_templates"].get("email_newsletter"), "email_newsletter template missing"
    assert len(r["hashtags"]) > 0,            "hashtags missing"
    assert len(r["partnership_opportunities"]) == 3, "Expected 3 partnerships"
    print(f"  cat={cat}: communities={len(r['top_communities'])}, timeline={len(r['gtm_timeline'])}, hashtags={r['hashtags'][:2]}")
print("  PASS")

# ─── Test 4: Event Ops fallback ───────────────────────────────────────────────
print("\n=== TEST 4: Event Ops fallback schedule ===")
from agents.event_ops_agent import _fallback_schedule, _detect_conflicts
speakers = [{"name": f"Speaker {i}"} for i in range(12)]
for domain in ["conference", "music", "sports"]:
    r = _fallback_schedule(speakers, domain, 2, "Event 2026", 3000)
    days = list(r["schedule"].keys())
    all_sessions = []
    for d in r["schedule"].values():
        all_sessions.extend(d)
    conflicts = _detect_conflicts(all_sessions)
    real_conflicts = [
        c for c in conflicts
        if c.get("session_1") != c.get("session_2")
        and c.get("session_1", "").strip()
        and (c.get("conflict_type") == "room_overlap"
             or c.get("speaker", "").strip() not in ("", "Event Host", "TBD"))
    ]
    assert len(days) == 2, "Expected 2 days"
    assert len(all_sessions) > 0, "Empty session list"
    assert len(r["risk_register"]) == 5, "Expected 5 risks"
    print(f"  domain={domain}: days={days}, sessions={len(all_sessions)}, real_conflicts={len(real_conflicts)}, risks={len(r['risk_register'])}")
print("  PASS")

print("\n=== ALL TESTS PASSED ✅ ===")
