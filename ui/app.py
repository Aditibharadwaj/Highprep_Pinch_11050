import streamlit as st
import sys, os, json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import ConferenceOrchestrator
from tools.data_loader import load_events, summarize_dataset, MUSIC_CATEGORIES, SPORTS_CATEGORIES

st.set_page_config(
    page_title="Event AI Planner",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium Dark Theme CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"]           { font-family: 'Inter', sans-serif !important; }
.stApp                               { background: linear-gradient(135deg, #060610 0%, #0d1117 60%, #060b14 100%); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0e1a 0%, #0d1117 100%) !important;
    border-right: 1px solid rgba(56,189,248,.12) !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption { color: #94a3b8 !important; }

/* ── Metric Cards ── */
[data-testid="metric-container"] {
    background: rgba(15,23,42,.85);
    border: 1px solid rgba(56,189,248,.15);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    backdrop-filter: blur(8px);
    transition: border-color .25s;
}
[data-testid="metric-container"]:hover { border-color: rgba(56,189,248,.4); }

/* ── Tabs ── */
/* Hide the phantom highlight bar / underline that Streamlit renders above the clickable tabs */
[data-baseweb="tab-highlight"],
[data-baseweb="tab-border"] { display: none !important; }

.stTabs [data-baseweb="tab-list"] {
    background: rgba(15,23,42,.7);
    border-radius: 14px;
    padding: 5px 6px;
    border: 1px solid rgba(56,189,248,.1);
    gap: 3px;
    margin-bottom: .5rem;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 10px !important;
    color: #64748b !important;
    font-weight: 500 !important;
    font-size: .82rem !important;
    border: none !important;
    transition: all .25s ease !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,#1d4ed8,#0891b2) !important;
    color: #fff !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 15px rgba(29,78,216,.35) !important;
}

/* ── Primary Button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#1d4ed8 0%,#0891b2 100%) !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 700 !important; color: white !important;
    box-shadow: 0 4px 20px rgba(29,78,216,.35) !important;
    transition: all .3s ease !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(29,78,216,.5) !important;
}

/* ── Alert boxes ── */
.stInfo    { background: rgba(14,165,233,.08) !important; border: 1px solid rgba(14,165,233,.25) !important; border-radius: 10px !important; }
.stSuccess { background: rgba(16,185,129,.08) !important; border: 1px solid rgba(16,185,129,.25) !important; border-radius: 10px !important; }
.stWarning { background: rgba(245,158,11,.08) !important; border: 1px solid rgba(245,158,11,.25) !important; border-radius: 10px !important; }
.stError   { background: rgba(239,68,68,.08)  !important; border: 1px solid rgba(239,68,68,.25)  !important; border-radius: 10px !important; }

/* ── Progress bar ── */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg,#1d4ed8,#0891b2) !important;
    border-radius: 4px !important;
}

/* ── Tables ── */
.stTable th {
    background: rgba(15,23,42,.9) !important;
    color: #38bdf8 !important;
    font-weight: 600 !important;
}

/* ── Textarea ── */
.stTextArea textarea {
    background: rgba(15,23,42,.8) !important;
    border: 1px solid rgba(56,189,248,.15) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: .85rem !important;
}

/* ── Divider ── */
hr { border-color: rgba(56,189,248,.1) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar                  { width: 5px; height: 5px; }
::-webkit-scrollbar-track            { background: rgba(15,23,42,.5); }
::-webkit-scrollbar-thumb            { background: rgba(56,189,248,.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover      { background: rgba(56,189,248,.5); }

/* ── Hero Header ── */
.hero-header {
    background: linear-gradient(135deg,rgba(29,78,216,.1) 0%,rgba(8,145,178,.08) 50%,rgba(29,78,216,.06) 100%);
    border: 1px solid rgba(56,189,248,.2);
    border-radius: 20px;
    padding: 1.75rem 2.5rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(10px);
    position: relative; overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute; top: -40%; right: -8%;
    width: 280px; height: 280px;
    background: radial-gradient(circle,rgba(29,78,216,.07),transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-size: 2rem; font-weight: 800; letter-spacing: -.5px;
    background: linear-gradient(135deg,#f0f9ff,#38bdf8,#818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    margin: 0 0 .4rem 0;
}
.hero-badge {
    display: inline-flex; align-items: center; gap: .3rem;
    background: linear-gradient(135deg,rgba(29,78,216,.25),rgba(8,145,178,.25));
    border: 1px solid rgba(56,189,248,.3);
    padding: .2rem .75rem; border-radius: 20px;
    font-size: .78rem; font-weight: 600; color: #7dd3fc;
}
.hero-badge.rag {
    background: rgba(139,92,246,.2); border-color: rgba(139,92,246,.35); color: #c4b5fd;
}

/* ── Sidebar brand ── */
.sidebar-brand {
    font-size: 1.3rem; font-weight: 800;
    background: linear-gradient(135deg,#38bdf8,#818cf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

/* ── Section card ── */
.stat-card {
    background: rgba(15,23,42,.7);
    border: 1px solid rgba(56,189,248,.12);
    border-radius: 14px; padding: 1.25rem;
}

/* ── Negotiation tip ── */
.tip-card {
    background: rgba(15,23,42,.6);
    border-left: 3px solid #38bdf8;
    padding: .5rem 1rem;
    border-radius: 0 8px 8px 0;
    margin: .3rem 0;
    color: #cbd5e1; font-size: .88rem;
}

/* ── RAG badge inline ── */
.rag-badge {
    display: inline-flex; align-items: center; gap: .3rem;
    background: rgba(139,92,246,.15); border: 1px solid rgba(139,92,246,.3);
    padding: .15rem .6rem; border-radius: 20px;
    font-size: .72rem; font-weight: 600; color: #c4b5fd;
}
</style>
""", unsafe_allow_html=True)


# ── Domain helpers ────────────────────────────────────────────────────────────
def get_domain_label(category: str) -> str:
    if category == "Music Festival" or category in MUSIC_CATEGORIES:  return "music"
    if category == "Sports"         or category in SPORTS_CATEGORIES: return "sports"
    return "conference"

DOMAIN_ICONS    = {"conference": "🎯", "music": "🎵", "sports": "🏆"}
TALENT_LABEL    = {"conference": "Speakers", "music": "Artists", "sports": "Athletes / Performers"}
EXHIBITOR_LABEL = {"conference": "Exhibitors", "music": "Brand Activations", "sports": "Partner Zones"}

# ── Currency helpers ──────────────────────────────────────────────────────────
GEO_CURRENCY = {
    "India":     {"symbol": "₹",  "name": "INR", "flag": "🇮🇳"},
    "USA":       {"symbol": "$",  "name": "USD", "flag": "🇺🇸"},
    "Europe":    {"symbol": "£",  "name": "GBP", "flag": "🇪🇺"},
    "Singapore": {"symbol": "S$", "name": "SGD", "flag": "🇸🇬"},
}

def get_currency(geo: str) -> dict:
    """Return {'symbol': '₹', 'name': 'INR', 'flag': '🇮🇳'} for the given geography."""
    return GEO_CURRENCY.get(geo, {"symbol": "$", "name": "USD", "flag": "🌐"})

def fmt_price(value, geo: str, decimals: int = 0) -> str:
    """Format a numeric price with the correct currency symbol for the geography."""
    sym = get_currency(geo)["symbol"]
    try:
        v = float(value)
        if decimals == 0:
            return f"{sym}{v:,.0f}"
        return f"{sym}{v:,.{decimals}f}"
    except (TypeError, ValueError):
        return f"{sym}{value}"

# ── Fixed categories per problem statement ────────────────────────────────────
FIXED_CATEGORIES = ["AI", "Web3", "ClimateTech", "Music Festival", "Sports"]

# Load summary stats but ALWAYS restrict geography to exactly these 4 regions
try:
    _all_events = load_events()
    _summary    = summarize_dataset(_all_events)
except Exception:
    _all_events = []
    _summary    = {"total_events": 0, "conference": 0, "music": 0, "sports": 0, "geographies": []}

# Fixed to exactly these 4 regions per product specification
_geos = ["Europe", "India", "Singapore", "USA"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">🎯 Event AI Planner</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#475569;font-size:.78rem;margin-top:0;margin-bottom:.75rem">Powered by Multi-Agent AI · RAG-Enhanced</p>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="color:#38bdf8;font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:.5rem">Event Details</p>', unsafe_allow_html=True)

    event_name    = st.text_input("Event Name", "AI Summit Europe 2026")
    category      = st.selectbox("Category", FIXED_CATEGORIES)
    domain        = get_domain_label(category)

    st.markdown(
        f'<span style="display:inline-flex;align-items:center;gap:.3rem;background:rgba(29,78,216,.15);'
        f'border:1px solid rgba(56,189,248,.25);padding:.2rem .7rem;border-radius:20px;'
        f'font-size:.75rem;font-weight:600;color:#7dd3fc;margin:.25rem 0 .5rem 0;display:inline-block">'
        f'{DOMAIN_ICONS[domain]} Domain: {domain.title()}</span>',
        unsafe_allow_html=True,
    )

    geography = st.selectbox("Geography", _geos)
    city      = st.text_input("City", "London")

    st.markdown("---")
    st.markdown('<p style="color:#38bdf8;font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:.5rem">Event Parameters</p>', unsafe_allow_html=True)

    audience_size = st.slider("Expected Audience", 500, 300_000, 3_000, step=500)
    budget        = st.selectbox("Budget Level", ["low", "medium", "high"])
    event_date    = st.text_input("Event Date", "2026-09-15")
    event_days    = st.number_input("Duration (Days)", 1, 7, 2)
    num_speakers  = st.slider(f"No. of {TALENT_LABEL[domain]}", 5, 30, 10)

    st.markdown("---")
    generate = st.button("🚀 Generate AI Plan", type="primary", use_container_width=True)

    st.markdown(
        '<p style="color:#334155;font-size:.68rem;text-align:center;margin-top:.4rem">'
        '7 AI Agents · ChromaDB RAG · LLM-Powered</p>',
        unsafe_allow_html=True,
    )


# ── Landing page (before generate) ───────────────────────────────────────────
if not generate:
    st.markdown(f"""
    <div class="hero-header">
      <div class="hero-title">{DOMAIN_ICONS[domain]} AI-Powered Event Planner</div>
      <div style="color:#94a3b8;font-size:.92rem;margin-bottom:.9rem">
        End-to-end multi-agent system for conference &amp; event planning — sponsor discovery,
        talent matching, venue intelligence, pricing AI, GTM strategy, and schedule building.
      </div>
      <div style="display:flex;gap:.5rem;flex-wrap:wrap">
        <span class="hero-badge">💼 Sponsor Discovery</span>
        <span class="hero-badge">🎤 Talent Matching</span>
        <span class="hero-badge">🏢 Exhibitor Intel</span>
        <span class="hero-badge">📍 Venue Recommend</span>
        <span class="hero-badge">📈 Pricing AI</span>
        <span class="hero-badge">🚀 GTM Strategy</span>
        <span class="hero-badge">📋 Schedule Builder</span>
        <span class="hero-badge rag">🔍 RAG-Enhanced</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, icon, title, desc in [
        (c1, "🤖", "7 Specialized Agents",
         "Sponsor · Speaker · Exhibitor · Venue · Pricing · GTM · Ops — each powered by LLM + historical dataset"),
        (c2, "🔍", "RAG Vector Search",
         "ChromaDB semantic search over past events gives every agent richer, grounded context beyond keyword filters"),
        (c3, "🌐", "3-Domain Coverage",
         "Conferences · Music Festivals · Sporting Events — domain-agnostic architecture with shared orchestrator"),
    ]:
        with col:
            st.markdown(f"""
            <div class="stat-card">
              <div style="font-size:1.6rem;margin-bottom:.4rem">{icon}</div>
              <div style="font-weight:700;color:#e2e8f0;margin-bottom:.3rem">{title}</div>
              <div style="font-size:.82rem;color:#64748b">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 Configure your event in the sidebar and click **Generate AI Plan** to begin.")
    st.stop()


# ── Shared Plotly dark-theme layout ──────────────────────────────────────────
_PL = dict(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    font_color="#94a3b8", margin=dict(l=10, r=110, t=20, b=10),
)

# ── Run orchestrator ──────────────────────────────────────────────────────────
AGENT_ORDER  = ["sponsor", "speaker", "exhibitor", "venue", "pricing", "gtm", "event_ops"]
AGENT_LABELS = {
    "sponsor": "💼 Sponsor", "speaker": "🎤 Speaker", "exhibitor": "🏢 Exhibitor",
    "venue": "📍 Venue", "pricing": "📈 Pricing", "gtm": "🚀 GTM", "event_ops": "📋 Event Ops",
}
completed = []

st.markdown(f"""
<div class="hero-header">
  <div class="hero-title">{DOMAIN_ICONS[domain]} {event_name}</div>
  <div style="color:#94a3b8;font-size:.88rem;display:flex;gap:1.5rem;flex-wrap:wrap;margin-top:.4rem">
    <span>📍 {city}, {geography}</span>
    <span>👥 {audience_size:,} attendees</span>
    <span>📅 {event_date} · {event_days} day(s)</span>
    <span>💰 {budget.title()} budget</span>
    <span class="hero-badge rag" style="font-size:.72rem">🔍 RAG Active</span>
  </div>
</div>
""", unsafe_allow_html=True)

progress_bar  = st.progress(0)
status_text   = st.empty()
pipeline_slot = st.empty()


def _render_pipeline(done: list) -> str:
    html = '<div style="display:flex;flex-wrap:wrap;gap:.4rem;margin:.4rem 0">'
    for a in AGENT_ORDER:
        if a in done:
            s = "background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.3);color:#6ee7b7"
            ic = "✅"
        else:
            s = "background:rgba(15,23,42,.6);border:1px solid rgba(56,189,248,.08);color:#475569"
            ic = "⏳"
        html += (f'<span style="{s};display:inline-flex;align-items:center;gap:.3rem;'
                 f'padding:.3rem .8rem;border-radius:8px;font-size:.8rem;font-weight:500">'
                 f'{ic} {AGENT_LABELS[a]}</span>')
    html += "</div>"
    return html


def on_progress(agent, status):
    if status == "done":
        completed.append(agent)
    pct = int(len(completed) / len(AGENT_ORDER) * 100)
    progress_bar.progress(pct)
    lbl = AGENT_LABELS.get(agent, agent.title())
    if status == "done":
        status_text.markdown(
            f'<span style="color:#6ee7b7;font-size:.85rem;font-weight:600">✅ {lbl} complete</span>',
            unsafe_allow_html=True,
        )
    else:
        status_text.markdown(
            f'<span style="color:#38bdf8;font-size:.85rem;font-weight:600">⚡ Running {lbl}...</span>',
            unsafe_allow_html=True,
        )
    pipeline_slot.markdown(_render_pipeline(completed), unsafe_allow_html=True)


with st.spinner(""):
    orch = ConferenceOrchestrator()
    plan = orch.run(
        event_name=event_name, category=category, geography=geography,
        city=city, audience_size=audience_size, budget=budget,
        event_date=event_date, event_days=int(event_days), num_speakers=num_speakers,
        progress_callback=on_progress,
    )

progress_bar.progress(100)
status_text.empty()
pipeline_slot.markdown(_render_pipeline(AGENT_ORDER), unsafe_allow_html=True)
st.success(f"✅ **{event_name}** — plan generated by {len(AGENT_ORDER)} AI agents")

st.divider()

# ── Tab bar ───────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "💼 Sponsors",
    f"🎤 {TALENT_LABEL[domain]}",
    f"🏢 {EXHIBITOR_LABEL[domain]}",
    "📍 Venues",
    "📈 Pricing",
    "🚀 GTM",
    "📋 Schedule",
    "📄 Export",
])

_RAG_PILL = ('<span class="rag-badge">🔍 RAG-Enhanced</span><br><br>')


# ════════════════════════════════════════════════════════
# TAB 0 — SPONSORS
# ════════════════════════════════════════════════════════
with tabs[0]:
    data = plan.get("sponsors", {})
    if "error" in data:
        st.error(data["error"]); st.stop()

    if data.get("rag_used"):
        st.markdown(_RAG_PILL, unsafe_allow_html=True)

    ranked = data.get("dataset_ranked_sponsors", [])
    if ranked:
        st.markdown("#### 📊 Relevance-Ranked Sponsors")
        st.caption("Scoring: Industry relevance 35% · Geo frequency 25% · Historical frequency 20% · Audience overlap 20%")
        tier_colors = {"Platinum": "#38bdf8", "Gold": "#fbbf24", "Silver": "#94a3b8", "Bronze": "#a16207"}
        fig = go.Figure(go.Bar(
            y=[s["name"] for s in ranked[:12]],
            x=[s["relevance_score"] for s in ranked[:12]],
            orientation="h",
            marker_color=[tier_colors.get(s.get("tier", "Bronze"), "#94a3b8") for s in ranked[:12]],
            marker_line_width=0,
            text=[f"{s.get('tier','?')}  ·  {s['relevance_score']}/100" for s in ranked[:12]],
            textposition="outside",
            textfont=dict(color="#94a3b8", size=11),
        ))
        fig.update_layout(
            height=370,
            xaxis=dict(title="Relevance Score", range=[0, 125], gridcolor="rgba(56,189,248,.06)"),
            yaxis=dict(autorange="reversed"),
            **_PL,
        )
        st.plotly_chart(fig, use_container_width=True)

        l1, l2, l3, l4 = st.columns(4)
        l1.markdown('<span style="color:#38bdf8;font-weight:700">🔵 Platinum</span> ≥ 80', unsafe_allow_html=True)
        l2.markdown('<span style="color:#fbbf24;font-weight:700">🟡 Gold</span> ≥ 65',    unsafe_allow_html=True)
        l3.markdown('<span style="color:#94a3b8;font-weight:700">⬜ Silver</span> ≥ 50',  unsafe_allow_html=True)
        l4.markdown('<span style="color:#a16207;font-weight:700">🟫 Bronze</span> < 50',  unsafe_allow_html=True)

    st.divider()
    recs = data.get("recommended_sponsors", [])
    adds = data.get("additional_suggestions", [])

    col_rec, col_add = st.columns([3, 2])
    with col_rec:
        if recs:
            st.markdown("#### 🏆 Recommended Sponsors")
            icons = {"Platinum": "🥇", "Gold": "🥈", "Silver": "🥉", "Bronze": "🏅"}
            for sp in recs:
                with st.expander(f"{icons.get(sp.get('tier','Bronze'),'🏅')} {sp['name']}  ·  {sp.get('tier','?')}  ·  Score: {sp.get('priority_score','?')}/10"):
                    st.write(f"**Why:** {sp.get('reason', '')}")
    with col_add:
        if adds:
            st.markdown("#### 💡 New Suggestions")
            for sp in adds:
                st.info(f"**{sp['name']}**\n\n{sp.get('reason', '')}")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        outline = data.get("proposal_outline", [])
        if outline:
            st.markdown("#### 📋 Proposal Outline")
            for b in outline:
                st.markdown(f"▸ {b}")
    with c2:
        email = data.get("outreach_email_template", "")
        if email:
            st.markdown("#### ✉️ Outreach Email Template")
            st.text_area("", email, height=210, label_visibility="collapsed")


# ════════════════════════════════════════════════════════
# TAB 1 — SPEAKERS / ARTISTS / ATHLETES
# ════════════════════════════════════════════════════════
with tabs[1]:
    data = plan.get("speakers", {})
    if "error" in data:
        st.error(data["error"]); st.stop()

    if data.get("rag_used"):
        st.markdown(_RAG_PILL, unsafe_allow_html=True)

    ranked = data.get("dataset_ranked_speakers", [])
    if ranked:
        st.markdown(f"#### 📊 Relevance-Ranked {TALENT_LABEL[domain]}")
        st.caption("Scoring: Topic/genre relevance 30% · Experience 25% · Influence 25% · Geo preference 20%")
        fig = go.Figure(go.Bar(
            y=[s["name"] for s in ranked[:12]],
            x=[s["relevance_score"] for s in ranked[:12]],
            orientation="h",
            marker_color="#0891b2",
            marker_line_width=0,
            text=[f"Score: {s['relevance_score']} · Apps: {s.get('frequency',0)}" for s in ranked[:12]],
            textposition="outside",
            textfont=dict(color="#94a3b8", size=11),
        ))
        fig.update_layout(
            height=370,
            xaxis=dict(title="Relevance Score", range=[0, 125], gridcolor="rgba(56,189,248,.06)"),
            yaxis=dict(autorange="reversed"),
            **_PL,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    speakers = data.get("recommended_speakers", [])
    if speakers:
        st.markdown(f"#### 🎤 Recommended {TALENT_LABEL[domain]}")
        type_icons = {
            "keynote": "🎤", "panel": "👥", "workshop": "🛠️",
            "headliner": "⭐", "opener": "🎶", "athlete": "🏅", "performer": "🎸",
        }
        cols = st.columns(2)
        for i, sp in enumerate(speakers):
            icon = type_icons.get(str(sp.get("type", "")).lower(), "🎤")
            with cols[i % 2]:
                with st.expander(f"{icon} {sp['name']}  ·  {sp.get('type','').title()}"):
                    st.write(f"**Expertise / Genre:** {sp.get('expertise', '')}")
                    st.write(f"**Slot / Talk:** _{sp.get('suggested_talk_title', '')}_")
                    st.write(f"**Why:** {sp.get('reason', '')}")

    themes = data.get("keynote_themes", [])
    if themes:
        st.divider()
        st.markdown("#### 💡 Headline Themes")
        t_n = min(len(themes), 3)
        t_cols = st.columns(t_n)
        for i, t in enumerate(themes[:t_n]):
            with t_cols[i]:
                st.markdown(
                    f'<div class="stat-card"><span style="color:#38bdf8;font-weight:700;font-size:.8rem">'
                    f'Theme {i+1}</span><br><span style="color:#e2e8f0;font-size:.9rem">{t}</span></div>',
                    unsafe_allow_html=True,
                )

    insight = data.get("historical_insight", "")
    if insight:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"📊 {insight}")


# ════════════════════════════════════════════════════════
# TAB 2 — EXHIBITORS / BRAND ACTIVATIONS / PARTNER ZONES
# ════════════════════════════════════════════════════════
with tabs[2]:
    data = plan.get("exhibitors", {})
    if "error" in data:
        st.error(data["error"]); st.stop()

    clusters_ds  = data.get("dataset_clustered_exhibitors", {})
    clusters_llm = data.get("exhibitor_clusters", {})

    if clusters_ds:
        st.markdown(f"#### 📊 {EXHIBITOR_LABEL[domain]} Distribution")
        names  = list(clusters_ds.keys())
        values = [len(v) for v in clusters_ds.values()]
        fig    = px.pie(
            names=names, values=values,
            color_discrete_sequence=["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f87171"],
            hole=0.4,
        )
        fig.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8", margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        )
        fig.update_traces(textfont_color="#e2e8f0")
        st.plotly_chart(fig, use_container_width=True)

    if clusters_llm:
        st.divider()
        st.markdown(f"#### 🏢 Recommended {EXHIBITOR_LABEL[domain]}")
        pitches = data.get("cluster_pitch", {})
        for cluster_name, items in clusters_llm.items():
            pitch = pitches.get(cluster_name, "")
            with st.expander(f"**{cluster_name}** — {len(items)} entries{(' · ' + pitch) if pitch else ''}"):
                for item in items:
                    st.markdown(f"▸ **{item['name']}** — {item.get('reason', '')}")

    booth = data.get("booth_pricing", {})
    if booth:
        st.divider()
        st.markdown("#### 💰 Booth / Zone Pricing")
        rows = [{
            "Tier": tn,
            "Price": d.get("price", "—"),
            "Includes": " · ".join(d.get("includes", [])),
        } for tn, d in booth.items()]
        st.table(pd.DataFrame(rows))

    est = data.get("total_exhibitor_revenue_estimate", "")
    if est:
        st.success(f"💰 Estimated Exhibitor Revenue: **{est}**")


# ════════════════════════════════════════════════════════
# TAB 3 — VENUES
# ════════════════════════════════════════════════════════
with tabs[3]:
    data = plan.get("venues", {})
    if "error" in data:
        st.error(data["error"]); st.stop()

    ctx_v = data.get("dataset_venue_context", {})
    if ctx_v:
        v1, v2, v3 = st.columns(3)
        v1.metric("Past Events in City",   ctx_v.get("past_events_in_city", 0))
        v2.metric("Past Events in Region", ctx_v.get("past_events_in_region", 0))
        v3.metric("Avg Audience (Region)", f"{int(ctx_v.get('avg_audience_in_region', 0)):,}")

    top_pick   = data.get("top_pick", "")
    top_reason = data.get("top_pick_reason", "")
    if top_pick:
        st.success(f"🏆 **Top Pick: {top_pick}** — {top_reason}")

    venues = data.get("recommended_venues", [])
    if venues:
        st.divider()
        st.markdown("#### 📍 Recommended Venues")
        tier_icons = {"budget": "💚", "standard": "🔵", "premium": "💎"}
        for v in venues:
            icon = tier_icons.get(str(v.get("tier", "")).lower(), "⚪")
            cap  = v.get("capacity", 0)
            cap_str = f"{cap:,}" if isinstance(cap, (int, float)) else str(cap)
            with st.expander(f"{icon} {v['name']}  ·  {v.get('daily_rental_estimate','')}  ·  Cap: {cap_str}"):
                st.write(f"**Address:** {v.get('address', '')}")
                st.write(f"**Why it fits:** {v.get('why_it_fits', '')}")

                scores = v.get("scores", {})
                if scores:
                    cats  = list(scores.keys())
                    vals  = [scores[k] for k in cats]
                    vals += vals[:1]; cats += cats[:1]
                    fig   = go.Figure(go.Scatterpolar(
                        r=vals, theta=cats, fill="toself",
                        line_color="#38bdf8", fillcolor="rgba(56,189,248,.1)",
                    ))
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 10], gridcolor="rgba(56,189,248,.1)"),
                            angularaxis=dict(gridcolor="rgba(56,189,248,.1)"),
                            bgcolor="rgba(0,0,0,0)",
                        ),
                        height=240, paper_bgcolor="rgba(0,0,0,0)",
                        margin=dict(l=40, r=40, t=20, b=20),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                past = v.get("past_events", [])
                if past and past[0]:
                    st.write("**Past events:** " + ", ".join(past))

    tips = data.get("negotiation_tips", [])
    if tips:
        st.divider()
        st.markdown("#### 💡 Negotiation Tips")
        for t in tips:
            st.markdown(f'<div class="tip-card">{t}</div>', unsafe_allow_html=True)

    if not data.get("recommended_venues") and not data.get("top_pick"):
        st.info("ℹ️ Venue data will appear here once the AI agent completes its analysis.")


# ════════════════════════════════════════════════════════
# TAB 4 — PRICING
# ════════════════════════════════════════════════════════
with tabs[4]:
    data = plan.get("pricing", {})
    if "error" in data:
        st.error(data["error"]); st.stop()

    _cur = get_currency(geography)
    st.markdown(
        f'<div style="display:inline-flex;align-items:center;gap:.4rem;'
        f'background:rgba(29,78,216,.12);border:1px solid rgba(56,189,248,.2);'
        f'padding:.3rem .9rem;border-radius:20px;font-size:.8rem;font-weight:600;color:#7dd3fc;margin-bottom:.75rem">'
        f'{_cur["flag"]} Currency: {_cur["name"]} ({_cur["symbol"]})</div>',
        unsafe_allow_html=True,
    )

    rp = data.get("recommended_pricing", {})
    # If LLM pricing is missing, build it from the dataset mean stats
    if not rp:
        _ds = data.get("dataset_stats", {})
        if _ds:
            rp = {
                "early_bird": {"price": _ds.get("early_bird", {}).get("mean", 0)},
                "standard":   {"price": _ds.get("standard",   {}).get("mean", 0)},
                "vip":        {"price": _ds.get("vip",        {}).get("mean", 0)},
            }
    if rp:
        st.markdown("#### 🎟️ Recommended Ticket Prices")
        p1, p2, p3 = st.columns(3)
        p1.metric("🌅 Early Bird",  fmt_price(rp.get('early_bird', {}).get('price', 0), geography))
        p2.metric("🎫 Normal / Standard", fmt_price(rp.get('standard',   {}).get('price', 0), geography))
        p3.metric("💎 VIP",         fmt_price(rp.get('vip',        {}).get('price', 0), geography))
        rationale = data.get("pricing_rationale", "")
        if rationale:
            st.caption(f"💡 {rationale}")
        weeks = rp.get("early_bird", {}).get("open_weeks_before", 0)
        if weeks:
            st.info(f"🗓️ Open Early Bird **{weeks} weeks** before event to maximise conversion.")
    else:
        st.warning("⚠️ Pricing data could not be calculated. Check the dataset or re-run the plan.")

    st.divider()
    att = data.get("dataset_attendance_prediction", {})
    rev = data.get("dataset_revenue_scenarios", {})

    if att:
        st.markdown("#### 👥 Attendance Prediction")
        a1, a2, a3 = st.columns(3)
        a1.metric("📉 Conservative", f"{att.get('conservative', 0):,}")
        a2.metric("📊 Base Case",    f"{att.get('base_case', 0):,}")
        a3.metric("📈 Optimistic",   f"{att.get('optimistic', 0):,}")
    else:
        st.info("ℹ️ Attendance prediction will appear here once the AI agent completes its analysis.")

    if rev:
        st.markdown(f"#### 💰 Revenue Scenarios ({_cur['name']})")
        scenarios = list(rev.keys())
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Ticket Revenue", x=scenarios,
                             y=[rev[s]["ticket_revenue"] for s in scenarios],
                             marker_color="#0891b2", marker_line_width=0))
        fig.add_trace(go.Bar(name="Total Revenue",  x=scenarios,
                             y=[rev[s]["total_revenue"]  for s in scenarios],
                             marker_color="#1d4ed8", marker_line_width=0))
        fig.add_trace(go.Bar(name="Profit",         x=scenarios,
                             y=[rev[s]["profit"]         for s in scenarios],
                             marker_color="#10b981", marker_line_width=0))
        fig.update_layout(
            barmode="group", height=320,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94a3b8",
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            xaxis=dict(gridcolor="rgba(56,189,248,.05)"),
            yaxis=dict(
                title=f"Amount ({_cur['symbol']})",
                gridcolor="rgba(56,189,248,.05)",
                tickprefix=_cur["symbol"],
            ),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)
        bev = data.get("dataset_breakeven_tickets", 0)
        st.metric("🎯 Break-even Tickets", f"{bev:,}")
        # Revenue table
        rev_rows = []
        for sc in scenarios:
            rev_rows.append({
                "Scenario":       sc.title(),
                "Ticket Revenue": fmt_price(rev[sc]["ticket_revenue"], geography),
                "Total Revenue":  fmt_price(rev[sc]["total_revenue"],  geography),
                "Profit":         fmt_price(rev[sc]["profit"],         geography),
            })
        st.table(pd.DataFrame(rev_rows))

    stats = data.get("dataset_stats", {})
    if stats:
        st.divider()
        st.markdown(f"#### 📜 Historical Pricing Stats ({_cur['name']})")
        rows = []
        for tier in ["early_bird", "standard", "vip"]:
            s = stats.get(tier, {})
            if s.get("count", 0) > 0:
                rows.append({
                    "Tier":   tier.replace("_", " ").title(),
                    "Mean":   fmt_price(s['mean'],   geography),
                    "Median": fmt_price(s['median'], geography),
                    "Min":    fmt_price(s['min'],    geography),
                    "Max":    fmt_price(s['max'],    geography),
                    "Events": s["count"],
                })
        if rows:
            st.table(pd.DataFrame(rows))
    else:
        st.info("ℹ️ Historical pricing statistics will appear here once the AI agent completes its analysis.")

    conv = data.get("conversion_rate_assumptions", {})
    if conv:
        st.divider()
        st.markdown("#### 🔄 Conversion Rate Assumptions")
        cr1, cr2, cr3 = st.columns(3)
        cr1.metric("🌅 Early Bird", conv.get("early_bird_conversion", "—"))
        cr2.metric("🎫 Standard",   conv.get("standard_conversion", "—"))
        cr3.metric("💎 VIP",        conv.get("vip_conversion", "—"))


# ════════════════════════════════════════════════════════
# TAB 5 — GTM
# ════════════════════════════════════════════════════════
with tabs[5]:
    data = plan.get("gtm", {})
    if "error" in data:
        st.error(data["error"]); st.stop()

    communities = data.get("top_communities", [])
    if communities:
        st.markdown("#### 🌐 Top Communities to Target")

        def _parse_reach(val: str) -> int:
            v = str(val).replace("k+", "000").replace("M+", "000000").replace("+", "").replace(",", "")
            try: return int(v)
            except: return 0

        fig = go.Figure(go.Bar(
            y=[c["name"] for c in communities],
            x=[_parse_reach(c.get("expected_reach", "0")) for c in communities],
            orientation="h",
            marker_color="#818cf8",
            marker_line_width=0,
            text=[c["platform"] for c in communities],
            textposition="outside",
            textfont=dict(color="#94a3b8", size=11),
        ))
        fig.update_layout(
            height=300, xaxis_title="Expected Reach",
            yaxis=dict(autorange="reversed"),
            **_PL,
        )
        st.plotly_chart(fig, use_container_width=True)

        cc = st.columns(2)
        for i, c in enumerate(communities):
            with cc[i % 2]:
                with st.expander(f"**{c['name']}** · {c['platform']} · Reach: {c.get('expected_reach','?')}"):
                    st.write(f"**Why:** {c.get('why', '')}")
                    st.write(f"**Posting frequency:** {c.get('posting_frequency', '')}")

    timeline = data.get("gtm_timeline", [])
    if timeline:
        st.divider()
        st.markdown("#### 📅 8-Week GTM Timeline")
        tl_rows = [{
            "Week":         f"Week {t['week']}",
            "Action":       t.get("action", ""),
            "Channels":     ", ".join(t.get("channels", [])),
            "Content Type": t.get("content_type", ""),
        } for t in timeline]
        st.table(pd.DataFrame(tl_rows))

    templates = data.get("message_templates", {})
    if templates:
        st.divider()
        st.markdown("#### ✍️ Message Templates")
        t1, t2, t3 = st.columns(3)
        with t1:
            if templates.get("discord_slack"):
                st.markdown("**Discord / Reddit**")
                st.text_area("", templates["discord_slack"], height=130, key="disc", label_visibility="collapsed")
        with t2:
            if templates.get("linkedin_post"):
                st.markdown("**LinkedIn / Instagram**")
                st.text_area("", templates["linkedin_post"], height=130, key="li", label_visibility="collapsed")
        with t3:
            if templates.get("email_newsletter"):
                st.markdown("**Email Newsletter**")
                st.text_area("", templates["email_newsletter"], height=130, key="em", label_visibility="collapsed")

    partners = data.get("partnership_opportunities", [])
    if partners:
        st.divider()
        st.markdown("#### 🤝 Partnership Opportunities")
        for p in partners:
            st.info(f"**{p.get('partner','')}** ({p.get('type','')}) — {p.get('value_exchange','')}")

    tags     = data.get("hashtags", [])
    keywords = data.get("seo_keywords", [])
    if tags or keywords:
        st.divider()
        hc, kc = st.columns(2)
        if tags:
            with hc:
                st.markdown("#### # Hashtags")
                st.write("  ".join([f"`{t}`" for t in tags]))
        if keywords:
            with kc:
                st.markdown("#### 🔍 SEO Keywords")
                st.write("  ".join([f"`{k}`" for k in keywords]))

    if not data.get("top_communities") and not data.get("gtm_timeline"):
        st.info("ℹ️ GTM strategy data will appear here once the AI agent completes its analysis.")


# ════════════════════════════════════════════════════════
# TAB 6 — SCHEDULE / EVENT OPS
# ════════════════════════════════════════════════════════
with tabs[6]:
    data = plan.get("event_ops", {})
    if "error" in data:
        st.error(data["error"]); st.stop()

    # ── Summary banner ──────────────────────────────────
    total_sessions = data.get("total_sessions", 0)
    domain_ops_label = {
        "conference": "Conference Schedule",
        "music":      "Festival Stage Plan",
        "sports":     "Match Schedule",
    }.get(data.get("domain", "conference"), "Event Schedule")

    all_sessions_flat = []
    for _d, _sl in data.get("schedule", {}).items():
        if isinstance(_sl, list):
            all_sessions_flat.extend(_sl)

    _unique_rooms    = len(set(s.get("room","") for s in all_sessions_flat if s.get("room")))
    _unique_speakers = len(set(s.get("speaker","") for s in all_sessions_flat
                               if s.get("speaker","").strip() and s.get("speaker","") not in ("Event Host","TBD","")))
    _total_days      = len(data.get("schedule", {}))

    if total_sessions or _total_days:
        st.markdown(
            f'<div class="hero-header" style="padding:1rem 1.5rem;margin-bottom:1rem">'
            f'<div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;margin-bottom:.5rem">'
            f'📋 {domain_ops_label} — {event_name}</div>'
            f'<div style="display:flex;gap:2rem;flex-wrap:wrap;color:#94a3b8;font-size:.85rem">'
            f'<span>📅 <b style="color:#38bdf8">{_total_days}</b> day(s)</span>'
            f'<span>🗓️ <b style="color:#38bdf8">{total_sessions or len(all_sessions_flat)}</b> sessions</span>'
            f'<span>🏠 <b style="color:#38bdf8">{_unique_rooms}</b> rooms/stages</span>'
            f'<span>🎤 <b style="color:#38bdf8">{_unique_speakers}</b> talent slots</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("ℹ️ The schedule is being built by the Event Ops AI agent. Please re-run to populate this tab.")

    # ── Per-day schedule tables ──────────────────────────
    schedule = data.get("schedule", {})
    if schedule:
        for day, sessions in schedule.items():
            if not isinstance(sessions, list) or not sessions:
                st.markdown(f"#### 📅 {day}")
                st.info(f"No sessions found for {day}. The AI agent may still be processing.")
                continue
            st.markdown(f"#### 📅 {day} — {len(sessions)} sessions")
            rows = [{
                "Time":                 s.get("time", ""),
                "Session":              s.get("session", ""),
                "Speaker / Performer":  s.get("speaker", ""),
                "Stage / Room":         s.get("room", ""),
                "Type":                 s.get("type", "").title(),
                "Duration (min)":       s.get("duration_mins", ""),
            } for s in sessions]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No schedule data available yet. The AI agent will populate this once complete.")

    # ── Rooms Table ──────────────────────────────────────
    rooms_required = data.get("rooms_required", [])
    if rooms_required:
        st.divider()
        st.markdown("#### 🏠 Rooms / Venues / Stages Required")
        room_rows = [{
            "Name":     r.get("name",""),
            "Capacity": f"{r.get('capacity',0):,}" if isinstance(r.get('capacity'), (int,float)) else str(r.get('capacity','—')),
            "Purpose":  r.get("purpose",""),
        } for r in rooms_required]
        st.table(pd.DataFrame(room_rows))
    else:
        st.markdown("#### 🏠 Rooms / Venues / Stages Required")
        st.info("ℹ️ Room allocation details will appear here after the Event Ops agent completes.")

    # ── Conflict Detection ───────────────────────────────
    conflicts = data.get("conflicts_detected", [])
    real = [c for c in conflicts
            if c.get("session_1") != c.get("session_2")
            and c.get("session_1", "").strip()
            and (c.get("conflict_type") == "room_overlap"
                 or c.get("speaker", "").strip() not in ("", "Event Host", "TBD", ""))]
    st.divider()
    st.markdown("#### 🚧 Conflict Detection & Scheduling Hindrances")
    st.caption("The system automatically detects room double-bookings and speaker/performer scheduling clashes.")
    if real:
        st.warning(f"⚠️ **{len(real)} scheduling conflict(s) detected** — review and resolve below")
        for c in real:
            if c["conflict_type"] == "room_overlap":
                st.error(f"🏠 **Room Conflict** — `{c.get('room','')}` is double-booked at `{c.get('time','')}`\n\n"
                         f"- Session 1: {c.get('session_1','')}\n- Session 2: {c.get('session_2','')}\n\n"
                         f"**✅ Fix:** Move one session to a different room or a different timeslot.")
            else:
                st.error(f"🎤 **Speaker Double-Booked** — `{c.get('speaker','')}` is scheduled in two sessions simultaneously\n\n"
                         f"- Session 1: {c.get('session_1','')}\n- Session 2: {c.get('session_2','')}\n\n"
                         f"**✅ Fix:** Reassign one session to a different speaker or shift its timeslot.")
    else:
        st.success("✅ No scheduling hindrances detected — all sessions are conflict-free.")

    # ── Resource Plan ─────────────────────────────────────
    rp = data.get("resource_plan", {})
    st.divider()
    st.markdown("#### 🧑‍💼 Resource Plan")
    if rp:
        r1, r2 = st.columns(2)
        r1.metric("👥 Staff Required",      rp.get("staff_required", "—"))
        r2.metric("🙋 Volunteers Required", rp.get("volunteer_required", "—"))
        av = rp.get("av_equipment", [])
        if av:
            st.markdown("**🎙️ A/V Equipment:**")
            av_cols = st.columns(min(len(av), 3))
            for i, item in enumerate(av):
                with av_cols[i % 3]:
                    st.markdown(
                        f'<div class="tip-card">🔊 {item}</div>',
                        unsafe_allow_html=True,
                    )
        catering = rp.get("catering_meals", [])
        if catering:
            st.markdown("**🍽️ Catering / Meals:**")
            for meal in catering:
                st.markdown(f"▸ {meal}")
    else:
        st.info("ℹ️ Resource planning details will appear here after the Event Ops agent completes.")

    # ── Risk Register ─────────────────────────────────────
    risks = data.get("risk_register", [])
    st.divider()
    st.markdown("#### ⚠️ Risk Register")
    if risks:
        st.caption("Top operational risks identified by the AI agent, with mitigation strategies.")
        prob_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        for r in risks:
            icon = prob_icons.get(r.get("probability", "").lower(), "⚪")
            with st.expander(f"{icon} {r.get('risk','')} · {r.get('probability','').title()}"):
                st.write(f"**Mitigation:** {r.get('mitigation', '')}")
    else:
        st.info("ℹ️ Risk register will appear here after the Event Ops agent completes.")


# ════════════════════════════════════════════════════════
# TAB 7 — EXPORT
# ════════════════════════════════════════════════════════
with tabs[7]:
    st.markdown("#### 📥 Download Full Plan")
    st.download_button(
        "⬇️ Download Full Plan (JSON)",
        data=json.dumps(plan, indent=2),
        file_name=f"{event_name.replace(' ','_')}_plan.json",
        mime="application/json",
        use_container_width=True,
        type="primary",
    )
    st.caption("The JSON file contains all agent outputs — dataset stats, LLM recommendations, RAG context, schedules, and GTM plans.")

    st.divider()
    st.markdown("#### 📋 Plan Summary")

    with st.expander("🎯 Event Overview", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Event Name:** {event_name}")
            st.markdown(f"**Category:** {category}")
            st.markdown(f"**Domain:** {DOMAIN_ICONS[domain]} {domain.title()}")
            st.markdown(f"**Geography:** {geography} · {city}")
        with col_b:
            st.markdown(f"**Audience Size:** {audience_size:,}")
            st.markdown(f"**Budget:** {budget.title()}")
            st.markdown(f"**Duration:** {event_days} day(s)")
            st.markdown(f"**Date:** {event_date}")

    sponsors_data = plan.get("sponsors", {})
    with st.expander("💼 Sponsors"):
        recs = sponsors_data.get("recommended_sponsors", [])
        adds = sponsors_data.get("additional_suggestions", [])
        ranked = sponsors_data.get("dataset_ranked_sponsors", [])
        if recs:
            st.markdown("**Recommended:**")
            for i, sp in enumerate(recs[:8], 1):
                st.markdown(f"{i}. **{sp['name']}** ({sp.get('tier','N/A')}) — {sp.get('reason','')}")
        elif ranked:
            st.markdown("**Top Ranked Sponsors (from dataset):**")
            for i, sp in enumerate(ranked[:8], 1):
                st.markdown(f"{i}. **{sp['name']}** — Score: {sp.get('relevance_score','N/A')} · Tier: {sp.get('tier','N/A')}")
        else:
            st.caption("No sponsor data available for this event.")
        if adds:
            st.markdown("**New Suggestions:**")
            for sp in adds:
                st.markdown(f"▸ {sp['name']} — {sp.get('reason','')}")

    speakers_data = plan.get("speakers", {})
    with st.expander(f"🎤 {TALENT_LABEL[domain]}"):
        recs = speakers_data.get("recommended_speakers", [])
        ranked_spk = speakers_data.get("dataset_ranked_speakers", [])
        if recs:
            for i, sp in enumerate(recs[:10], 1):
                st.markdown(f"{i}. **{sp['name']}** — {sp.get('expertise','')} — _{sp.get('suggested_talk_title','')}_")
        elif ranked_spk:
            st.markdown(f"**Top Ranked {TALENT_LABEL[domain]} (from dataset):**")
            for i, sp in enumerate(ranked_spk[:10], 1):
                st.markdown(f"{i}. **{sp['name']}** — Score: {sp.get('relevance_score','N/A')} · Appearances: {sp.get('frequency',0)}")
        else:
            st.caption(f"No {TALENT_LABEL[domain].lower()} data available for this event.")
        themes = speakers_data.get("keynote_themes", [])
        if themes:
            st.markdown("**Keynote Themes:**")
            for t in themes: st.markdown(f"▸ {t}")

    exhibitors_data = plan.get("exhibitors", {})
    with st.expander(f"🏢 {EXHIBITOR_LABEL[domain]}"):
        clusters = exhibitors_data.get("exhibitor_clusters", {})
        ds_clusters = exhibitors_data.get("dataset_clustered_exhibitors", {})
        if clusters:
            for cluster, items in clusters.items():
                st.markdown(f"**{cluster}:**")
                for item in items[:5]:
                    st.markdown(f"▸ {item.get('name','')}")
        elif ds_clusters:
            st.markdown("**Dataset Clusters:**")
            for cluster, items in ds_clusters.items():
                st.markdown(f"**{cluster}:**")
                for item in items[:5]:
                    st.markdown(f"▸ {item.get('name','')}")
        else:
            st.caption(f"No {EXHIBITOR_LABEL[domain].lower()} data available for this event.")
        pricing = exhibitors_data.get("booth_pricing", {})
        if pricing:
            st.markdown("**Booth / Zone Pricing:**")
            for tier, details in pricing.items():
                st.markdown(f"▸ **{tier}:** {details.get('price','N/A')}")

    venues_data = plan.get("venues", {})
    with st.expander("📍 Venues"):
        recs = venues_data.get("recommended_venues", [])
        for i, v in enumerate(recs[:5], 1):
            cap = v.get("capacity", "N/A")
            cap_str = f"{cap:,}" if isinstance(cap, (int, float)) else str(cap)
            st.markdown(f"{i}. **{v['name']}** — {v.get('address','')}")
            st.markdown(f"   Capacity: {cap_str} · Daily Rate: {v.get('daily_rental_estimate','N/A')}")
        top = venues_data.get("top_pick", "")
        if top:
            st.markdown(f"**🏆 Top Pick:** {top} — {venues_data.get('top_pick_reason','')}")

    pricing_data = plan.get("pricing", {})
    with st.expander("📈 Pricing & Revenue"):
        _cur_exp = get_currency(geography)
        st.caption(f"{_cur_exp['flag']} All prices in {_cur_exp['name']} ({_cur_exp['symbol']})")
        pricing_rec = pricing_data.get("recommended_pricing", {})
        if pricing_rec:
            st.markdown("**Ticket Tiers:**")
            for tier, details in pricing_rec.items():
                st.markdown(f"▸ **{tier.replace('_',' ').title()}:** {fmt_price(details.get('price',0), geography)}")
        rev_scenarios = pricing_data.get("dataset_revenue_scenarios", {})
        if rev_scenarios:
            st.markdown("**Revenue Scenarios:**")
            for scenario, details in rev_scenarios.items():
                st.markdown(f"▸ **{scenario.title()}:** Revenue {fmt_price(details.get('total_revenue',0), geography)} · Profit {fmt_price(details.get('profit',0), geography)}")

    gtm_data = plan.get("gtm", {})
    with st.expander("🚀 Go-to-Market"):
        communities = gtm_data.get("top_communities", [])
        for c in communities[:6]:
            st.markdown(f"▸ **{c['name']}** ({c['platform']}) — {c.get('expected_reach','N/A')} reach")
        hashtags = gtm_data.get("hashtags", [])
        if hashtags:
            st.markdown(f"**Hashtags:** {', '.join(hashtags)}")

    ops_data = plan.get("event_ops", {})
    with st.expander("📋 Schedule"):
        schedule = ops_data.get("schedule", {})
        for day, sessions in schedule.items():
            if isinstance(sessions, list) and sessions:
                st.markdown(f"**{day}:** {len(sessions)} sessions")
        rc = [c for c in ops_data.get("conflicts_detected", [])
              if c.get("session_1") != c.get("session_2") and c.get("session_1","").strip()]
        if rc:
            st.markdown(f"⚠️ **Conflicts:** {len(rc)}")
        else:
            st.markdown("✅ **No conflicts detected**")
        ts = ops_data.get("total_sessions", 0)
        if ts:
            st.markdown(f"**Total Sessions:** {ts}")