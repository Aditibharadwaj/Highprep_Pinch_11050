# agents/orchestrator.py

import json
from tools.data_loader import load_events, summarize_dataset

def _import_agents():
    from agents import sponsor_agent, speaker_agent, exhibitor_agent
    from agents import venue_agent, pricing_agent, gtm_agent, event_ops_agent
    return {
        "sponsor":    sponsor_agent,
        "speaker":    speaker_agent,
        "exhibitor":  exhibitor_agent,
        "venue":      venue_agent,
        "pricing":    pricing_agent,
        "gtm":        gtm_agent,
        "event_ops":  event_ops_agent,
    }


class ConferenceOrchestrator:
    def __init__(self, data_path: str = None):
        self.events  = load_events(data_path) if data_path else load_events()
        self.summary = summarize_dataset(self.events)
        print(f"[Orchestrator] Loaded {self.summary['total_events']} events.")

        # ── Build RAG vector store (ChromaDB) ─────────────────────────────────
        self.rag_ready = False
        try:
            from tools.embeddings import build_vector_store
            build_vector_store(self.events)
            self.rag_ready = True
            print("[Orchestrator] RAG vector store ready.")
        except Exception as e:
            print(f"[Orchestrator] RAG unavailable (continuing without it): {e}")

        self.agents        = _import_agents()
        self.shared_memory = {}

    def run(
        self,
        event_name,
        category,
        geography,
        city,
        audience_size,
        budget="medium",
        event_date="TBD",
        event_days=2,
        num_speakers=10,
        progress_callback=None,
    ):

        def _update(agent, status):
            if callable(progress_callback):
                progress_callback(agent, status)

        plan = {}

        # Sponsor
        _update("sponsor", "running")
        plan["sponsors"] = self.agents["sponsor"].run(
            self.events, category, geography, audience_size, event_name,
            memory=self.shared_memory, rag_ready=self.rag_ready,
        )
        self.shared_memory["sponsors"] = plan["sponsors"]
        _update("sponsor", "done")

        # Speaker
        _update("speaker", "running")
        plan["speakers"] = self.agents["speaker"].run(
            self.events, category, geography, audience_size, event_name, num_speakers,
            memory=self.shared_memory, rag_ready=self.rag_ready,
        )
        self.shared_memory["speakers"] = plan["speakers"]
        _update("speaker", "done")

        # Exhibitor
        _update("exhibitor", "running")
        plan["exhibitors"] = self.agents["exhibitor"].run(
            self.events, category, geography, audience_size, budget, event_name
        )
        self.shared_memory["exhibitors"] = plan["exhibitors"]
        _update("exhibitor", "done")

        # Venue
        _update("venue", "running")
        plan["venues"] = self.agents["venue"].run(
            self.events, category, geography, city, audience_size, budget, event_name
        )
        self.shared_memory["venues"] = plan["venues"]
        _update("venue", "done")

        # Pricing
        _update("pricing", "running")
        plan["pricing"] = self.agents["pricing"].run(
            self.events, category, geography, audience_size, budget, event_name,
            memory=self.shared_memory,
        )
        self.shared_memory["pricing"] = plan["pricing"]
        _update("pricing", "done")

        # GTM
        _update("gtm", "running")
        plan["gtm"] = self.agents["gtm"].run(
            self.events, category, geography, audience_size, event_name, event_date,
            memory=self.shared_memory,
        )
        self.shared_memory["gtm"] = plan["gtm"]
        _update("gtm", "done")

        # Event Ops
        _update("event_ops", "running")
        speakers_list = plan["speakers"].get("recommended_speakers", [])
        plan["event_ops"] = self.agents["event_ops"].run(
            speakers_list, category, geography, audience_size,
            event_name, event_days,
            memory=self.shared_memory,
        )
        _update("event_ops", "done")

        return plan