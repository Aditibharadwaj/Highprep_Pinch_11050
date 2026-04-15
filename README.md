# Conference AI — Multi-Agent Conference Planner

An end-to-end AI-powered multi-agent system for conference organization, built for the Pinch × IIT Roorkee General Championship 2026.

## Architecture

```
conference-ai/
├── data/
│   └── events_merged_2025_2026.xlsx   ← Your merged dataset (69 events)
├── agents/
│   ├── orchestrator.py                ← Routes tasks between all agents
│   ├── sponsor_agent.py               ← Sponsor recommendations + outreach
│   ├── speaker_agent.py               ← Speaker discovery + agenda builder
│   ├── exhibitor_agent.py             ← Exhibitor clustering + booth pricing
│   ├── venue_agent.py                 ← Venue recommendations + scoring
│   ├── pricing_agent.py               ← Ticket pricing model + revenue forecast
│   ├── gtm_agent.py                   ← Community identification + GTM plan
│   └── event_ops_agent.py             ← Schedule builder + conflict detection
├── tools/
│   ├── data_loader.py                 ← Loads and filters the Excel dataset
│   └── embeddings.py                  ← ChromaDB vector store for RAG
├── ui/
│   └── app.py                         ← Streamlit frontend
├── setup.py                           ← One-time setup script
├── requirements.txt
└── .env.example
```

## Setup

### 1. Clone & Install

```bash
git clone https://github.com/your-team/conference-ai
cd conference-ai
pip install -r requirements.txt
```

### 2. Set Your API Key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

Or set it directly:
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Add Your Dataset

Place your merged Excel file at:
```
data/events_merged_2025_2026.xlsx
```

Expected columns:
- Event Name, Year, Category, Geography, City
- Audience Size, Actual Attendance
- Ticket Price Early, Ticket Price Standard, Ticket Price VIP
- Sponsors, Key Speakers, Key Exhibitors
- Website, Data Source

### 4. Run Setup (builds vector index)

```bash
python setup.py
```

### 5. Launch the App

```bash
streamlit run ui/app.py
```

Open http://localhost:8501 in your browser.

## How Each Agent Works

| Agent | Input | Output | Data Used |
|-------|-------|--------|-----------|
| Sponsor | category, geography, size | Top sponsors + email template | Historical sponsor frequency |
| Speaker | category, geography, size | Speaker list + agenda | Historical speaker frequency |
| Exhibitor | category, geography, budget | Clustered exhibitors + pricing | Historical exhibitor data |
| Venue | city, size, budget | 5 venues with scorecards | City tier + past events |
| Pricing | category, geography, size | 3 pricing tiers + revenue model | Historical price statistics |
| GTM | category, geography, date | Communities + 8-week plan | Curated Discord/Slack DB |
| Event Ops | speakers from above | Full schedule + risk register | Claude reasoning |

## Tech Stack

- **AI**: Anthropic Claude claude-sonnet-4-20250514 (all agent reasoning)
- **Vector DB**: ChromaDB + sentence-transformers (RAG)
- **Data**: Pandas + OpenPyXL (Excel processing)
- **ML**: NumPy + Scikit-learn (pricing regression)
- **UI**: Streamlit + Plotly (frontend)

## Data Sources

The dataset covers 69 unique events (2025–2026) across:
- **Geographies**: USA, Europe, India, Singapore
- **Categories**: AI, Web3, ClimateTech, SaaS, Music Festivals, Sports, Startup/Tech
- **Extraction method**: Manual curation from event websites, Eventbrite, LinkedIn Events, and Luma
- **Deduplication**: Matched on normalized Event Name + Year; XLSX version kept when conflicts existed

## Team

Built for Pinch × IIT Roorkee General Championship 2026.
