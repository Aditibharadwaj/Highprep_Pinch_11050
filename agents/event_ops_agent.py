"""
agents/event_ops_agent.py
Domain-aware ops: conference schedule / festival stage plan / sports match schedule.
"""
import json
from tools.data_loader import get_domain
from tools.llm import call_llm

def _detect_conflicts(sessions):
    conflicts = []
    for i, s1 in enumerate(sessions):
        for j, s2 in enumerate(sessions):
            if i >= j: continue
            if s1.get("room") == s2.get("room") and s1.get("time") == s2.get("time") and s1.get("room"):
                conflicts.append({"conflict_type":"room_overlap","session_1":s1.get("session"),
                                   "session_2":s2.get("session"),"room":s1.get("room"),"time":s1.get("time")})
            sp = s1.get("speaker","").strip()
            if sp and sp == s2.get("speaker","").strip() and s1.get("time") == s2.get("time"):
                conflicts.append({"conflict_type":"speaker_double_booked","speaker":sp,
                                   "session_1":s1.get("session"),"session_2":s2.get("session")})
    return conflicts

DOMAIN_OPS = {
    "conference": {
        "schedule_type":  "2-day conference schedule with parallel tracks",
        "time_range":     "9:00 AM to 6:00 PM",
        "session_types":  "keynotes, panels, workshops, networking breaks, lunch",
        "resource_key":   "rooms, AV equipment, catering, registration desk",
    },
    "music": {
        "schedule_type":  "multi-stage festival lineup",
        "time_range":     "2:00 PM to 2:00 AM",
        "session_types":  "headliner sets, supporting acts, DJ sets, silent disco, food/merch intermissions",
        "resource_key":   "stages, sound systems, lighting rigs, crowd barriers, medical tents",
    },
    "sports": {
        "schedule_type":  "match/event schedule with warm-up and broadcast slots",
        "time_range":     "10:00 AM to 10:00 PM",
        "session_types":  "matches, warm-up sessions, press conferences, award ceremonies, fan zone activations",
        "resource_key":   "playing arenas, broadcast trucks, press rooms, medical staff, security zones",
    },
}


def _fallback_schedule(speakers, domain, event_days, event_name, audience_size):
    """Generate a complete, conflict-free domain-aware schedule when LLM fails."""
    t    = [s.get("name", f"Speaker {i+1}") for i, s in enumerate(speakers[:14])] if speakers else [f"Speaker {i+1}" for i in range(12)]
    # Pad talent list so index access never fails
    while len(t) < 14:
        t.append("TBD")

    schedule = {}
    for day_num in range(1, event_days + 1):
        key = f"Day {day_num}"
        idx = (day_num - 1) * 6   # stagger talent per day

        if domain == "conference":
            sessions = [
                {"time": "9:00 AM",  "duration_mins": 30,  "session": "Registration & Welcome Coffee",                      "speaker": "",            "room": "Main Lobby",      "type": "registration", "capacity": 500},
                {"time": "9:30 AM",  "duration_mins": 60,  "session": f"{'Opening' if day_num==1 else 'Day '+str(day_num)} Keynote","speaker": t[idx % 14],  "room": "Main Stage",      "type": "keynote",      "capacity": 500},
                {"time": "10:30 AM", "duration_mins": 15,  "session": "Networking Coffee Break",                             "speaker": "",            "room": "Foyer",          "type": "break",        "capacity": 500},
                {"time": "10:45 AM", "duration_mins": 45,  "session": f"Panel: Future of {'AI & LLMs' if day_num==1 else 'Product & Growth'}", "speaker": ", ".join([t[(idx+1)%14], t[(idx+2)%14]]), "room": "Main Stage", "type": "panel", "capacity": 500},
                {"time": "10:45 AM", "duration_mins": 45,  "session": "Workshop: Hands-on Deep Dive",                       "speaker": t[(idx+3)%14],  "room": "Workshop Room A", "type": "workshop",    "capacity": 80},
                {"time": "12:00 PM", "duration_mins": 60,  "session": "Networking Lunch",                                   "speaker": "",            "room": "Dining Hall",    "type": "break",        "capacity": 500},
                {"time": "1:00 PM",  "duration_mins": 45,  "session": f"Keynote: Scaling Innovation in {event_name.split()[0]+' 2026' if event_name else '2026'}", "speaker": t[(idx+4)%14], "room": "Main Stage", "type": "keynote", "capacity": 500},
                {"time": "1:00 PM",  "duration_mins": 45,  "session": "Fireside Chat: Startup Journeys",                   "speaker": t[(idx+5)%14],  "room": "Stage B",        "type": "panel",       "capacity": 200},
                {"time": "2:00 PM",  "duration_mins": 60,  "session": "Breakout: Track A — Technical Deep Dive",           "speaker": t[(idx+6)%14],  "room": "Track A Room",  "type": "workshop",    "capacity": 120},
                {"time": "2:00 PM",  "duration_mins": 60,  "session": "Breakout: Track B — Business Strategy",             "speaker": t[(idx+7)%14],  "room": "Track B Room",  "type": "workshop",    "capacity": 120},
                {"time": "3:00 PM",  "duration_mins": 15,  "session": "Afternoon Coffee Break",                             "speaker": "",            "room": "Foyer",          "type": "break",        "capacity": 500},
                {"time": "3:15 PM",  "duration_mins": 45,  "session": "Lightning Talks (5 × 8 min)",                       "speaker": t[(idx+8)%14],  "room": "Main Stage",     "type": "panel",       "capacity": 500},
                {"time": "4:00 PM",  "duration_mins": 60,  "session": "Investor / Partner Roundtable",                     "speaker": t[(idx+9)%14],  "room": "Boardroom",     "type": "workshop",    "capacity": 40},
                {"time": "5:00 PM",  "duration_mins": 60,  "session": f"{'Closing Keynote & Day 1 Wrap-Up' if day_num==1 else 'Awards & Closing Ceremony'}","speaker": t[(idx+10)%14],"room": "Main Stage","type": "keynote","capacity": 500},
                {"time": "6:00 PM",  "duration_mins": 90,  "session": "Evening Networking & Cocktails",                    "speaker": "",            "room": "Terrace/Lounge", "type": "networking",  "capacity": 500},
            ]
        elif domain == "music":
            sessions = [
                {"time": "2:00 PM",  "duration_mins": 60,  "session": "Gates Open & DJ Warmup",           "speaker": "DJ Warmup",          "room": "Stage A",    "type": "opener",    "capacity": 10000},
                {"time": "2:00 PM",  "duration_mins": 60,  "session": "Silent Disco Warmup",              "speaker": "DJ Collective",     "room": "Silent Tent","type": "opener",    "capacity": 2000},
                {"time": "3:15 PM",  "duration_mins": 50,  "session": "Opening Act",                      "speaker": t[idx % 14],          "room": "Stage A",    "type": "opener",    "capacity": 10000},
                {"time": "3:15 PM",  "duration_mins": 50,  "session": "DJ Set — Stage B",                  "speaker": t[(idx+1)%14],        "room": "Stage B",    "type": "opener",    "capacity": 5000},
                {"time": "4:30 PM",  "duration_mins": 60,  "session": "Mid-Tier Performer",               "speaker": t[(idx+2)%14],        "room": "Stage A",    "type": "headliner", "capacity": 10000},
                {"time": "6:00 PM",  "duration_mins": 75,  "session": "Co-Headliner Set",                 "speaker": t[(idx+3)%14],        "room": "Stage A",    "type": "headliner", "capacity": 12000},
                {"time": "8:00 PM",  "duration_mins": 90,  "session": "Headline Act",                     "speaker": t[(idx+4)%14],        "room": "Main Stage", "type": "headliner", "capacity": 15000},
                {"time": "10:00 PM", "duration_mins": 120, "session": "After Show — DJ Closing Set",      "speaker": t[(idx+5)%14],        "room": "Stage B",    "type": "opener",    "capacity": 5000},
            ]
        else:  # sports
            sessions = [
                {"time": "10:00 AM", "duration_mins": 45,  "session": "Opening Ceremony & Parade",        "speaker": "Event Host",         "room": "Main Arena",   "type": "ceremony",    "capacity": 50000},
                {"time": "11:00 AM", "duration_mins": 90,  "session": f"Match 1: Group Stage",            "speaker": t[idx % 14],          "room": "Main Arena",   "type": "match",       "capacity": 50000},
                {"time": "12:45 PM", "duration_mins": 30,  "session": "Press Conference — Match 1",       "speaker": t[(idx+1)%14],        "room": "Press Room",   "type": "press",       "capacity": 200},
                {"time": "1:30 PM",  "duration_mins": 60,  "session": "Fan Zone Activation & Merch",     "speaker": "",                   "room": "Fan Zone",     "type": "activation",  "capacity": 20000},
                {"time": "2:30 PM",  "duration_mins": 90,  "session": f"Match 2: Group Stage",            "speaker": t[(idx+2)%14],        "room": "Main Arena",   "type": "match",       "capacity": 50000},
                {"time": "4:15 PM",  "duration_mins": 30,  "session": "Athlete Autograph Session",        "speaker": t[(idx+3)%14],        "room": "Hospitality",  "type": "activation",  "capacity": 500},
                {"time": "5:00 PM",  "duration_mins": 90,  "session": f"Match 3: Semifinal / Feature",   "speaker": t[(idx+4)%14],        "room": "Main Arena",   "type": "match",       "capacity": 50000},
                {"time": "7:00 PM",  "duration_mins": 60,  "session": "Closing Ceremony & Awards",        "speaker": "Event Host",         "room": "Main Arena",   "type": "ceremony",    "capacity": 50000},
            ]

        schedule[key] = sessions

    return {
        "schedule": schedule,
        "rooms_required": [
            {"name": "Main Stage / Main Arena", "capacity": max(audience_size, 500), "purpose": "Keynotes, headline acts, main matches"},
            {"name": "Stage B / Track B",       "capacity": max(audience_size // 3, 200), "purpose": "Parallel sessions / supporting acts"},
            {"name": "Workshop Room A",         "capacity": 120, "purpose": "Hands-on workshops & breakouts"},
            {"name": "Workshop Room B",         "capacity": 120, "purpose": "Breakout sessions & fireside chats"},
            {"name": "Networking Foyer",        "capacity": max(audience_size, 500), "purpose": "Coffee breaks, networking, registration"},
        ],
        "resource_plan": {
            "av_equipment":       ["LED Main Stage Display (4K)", "Line Array PA Sound System", "Wireless Microphones ×10", "Live Streaming & Recording Setup", "Breakout Room AV Kits ×4", "Confidence Monitors"],
            "catering_meals":     ["Morning Welcome Coffee & Pastries", "Networking Lunch", "Afternoon Refreshments", "Evening Cocktail Reception"],
            "staff_required":     max(20, audience_size // 100),
            "volunteer_required": max(15, audience_size // 150),
        },
        "risk_register": [
            {"risk": "Speaker / performer cancellation last minute",               "probability": "medium", "mitigation": "Maintain 3 backup speakers per slot; keep pre-recorded talks ready to broadcast."},
            {"risk": "Technical AV failure during keynote",                        "probability": "low",    "mitigation": "Full redundant AV setup ready; conduct tech rehearsals 24 hours before event."},
            {"risk": "Low ticket sales / attendance shortfall",                    "probability": "medium", "mitigation": "Track weekly registration KPIs; activate FOMO email campaign if <60% sold 2 weeks out."},
            {"risk": "Venue / catering delivery delays on event day",              "probability": "medium", "mitigation": "Build 90-minute setup buffer before doors open; hold secondary vendor contacts on standby."},
            {"risk": "Security incident or crowd safety issue",                    "probability": "low",    "mitigation": "Hire certified security firm; brief all staff on emergency procedures; establish evacuation routes."},
        ],
    }

def run(speakers, category, geography, audience_size, event_name="New Event", event_days=2, num_tracks=2, memory=None):
    domain      = get_domain(category)
    ops         = DOMAIN_OPS.get(domain, DOMAIN_OPS["conference"])
    talent_names= [s.get("name","") for s in speakers[:12]] if speakers else []

    context = {
        "event_name":       event_name,
        "event_type":       domain,
        "category":         category,
        "geography":        geography,
        "audience_size":    audience_size,
        "event_days":       event_days,
        "schedule_type":    ops["schedule_type"],
        "time_range":       ops["time_range"],
        "session_types":    ops["session_types"],
        "resource_focus":   ops["resource_key"],
        "confirmed_talent": talent_names,
        "num_parallel_tracks": num_tracks,
    }

    prompt = f"""You are an expert {domain} event operations manager.

Context:
{json.dumps(context, indent=2)}

Build a complete {event_days}-day {ops['schedule_type']}:
1. Create a full agenda: {ops['time_range']} each day.
2. Include: {ops['session_types']}.
3. Distribute talent across {num_tracks} parallel tracks/stages to avoid conflicts.
4. Plan resources: {ops['resource_key']}.
5. Include a risk register: top 5 risks + mitigation.

Respond ONLY in JSON:
{{
  "schedule": {{
    "Day 1": [
      {{"time":"9:00 AM","duration_mins":60,"session":"...","speaker":"...","room":"Main Stage","type":"keynote","capacity":0}}
    ],
    "Day 2": []
  }},
  "rooms_required": [{{"name":"...","capacity":0,"purpose":"..."}}],
  "resource_plan": {{
    "av_equipment":      ["..."],
    "catering_meals":    ["..."],
    "staff_required":    0,
    "volunteer_required":0
  }},
  "risk_register": [
    {{"risk":"...","probability":"high/medium/low","mitigation":"..."}}
  ],
  "conflicts_detected": []
}}"""

    raw = call_llm(prompt)
    raw = raw.replace("```json","").replace("```","").strip()
    try:
        result = json.loads(raw)
        if not result.get("schedule"):
            raise ValueError("Missing schedule")
    except Exception:
        # Fallback: generate a complete schedule so the tab never shows empty
        result = _fallback_schedule(speakers, domain, event_days, event_name, audience_size)

    all_sessions = []
    for day_sessions in result.get("schedule",{}).values():
        if isinstance(day_sessions, list):
            all_sessions.extend(day_sessions)

    result["conflicts_detected"] = _detect_conflicts(all_sessions)
    result["total_sessions"]     = len(all_sessions)
    result["domain"]             = domain
    return result