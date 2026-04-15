"""
tools/scoring.py
Scoring and ranking utilities for conference agents.
"""

import random
from typing import List, Dict, Any


def cluster_exhibitors(exhibitors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Cluster exhibitors based on frequency and type.
    Returns list of exhibitors with added 'cluster' key.
    """
    clusters = ["Startup", "Enterprise", "Tools/Platform", "Research", "Individual/Consultant"]
    
    for ex in exhibitors:
        # Simple clustering based on name patterns
        name = ex["name"].lower()
        if any(word in name for word in ["inc", "corp", "ltd", "enterprises"]):
            ex["cluster"] = "Enterprise"
        elif any(word in name for word in ["university", "research", "lab"]):
            ex["cluster"] = "Research"
        elif any(word in name for word in ["tools", "platform", "software", "api"]):
            ex["cluster"] = "Tools/Platform"
        elif any(word in name for word in ["consultant", "freelance", "individual"]):
            ex["cluster"] = "Individual/Consultant"
        else:
            ex["cluster"] = random.choice(clusters)  # Random for simplicity
    
    return exhibitors


def rank_speakers(candidates: List[Dict[str, Any]], category: str, geography: str) -> List[Dict[str, Any]]:
    """
    Rank speakers based on relevance to category and geography.
    """
    for candidate in candidates:
        # Simple scoring: experience + relevance
        experience_score = len(candidate.get("past_events", []))
        relevance_score = 0.5  # Base
        
        # Boost if topics match category
        if any(topic.lower() in category.lower() for topic in candidate.get("topics", [])):
            relevance_score += 0.3
        
        # Boost if geo matches
        if geography.lower() in candidate.get("geo", "").lower():
            relevance_score += 0.2
        
        candidate["relevance_score"] = min(relevance_score + experience_score * 0.1, 1.0)
    
    # Sort by relevance_score descending
    candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
    return candidates


def rank_sponsors(candidates: List[Dict[str, Any]], category: str, geography: str) -> List[Dict[str, Any]]:
    """
    Rank sponsors based on industry relevance and geography.
    """
    for candidate in candidates:
        relevance_score = candidate.get("audience_overlap_score", 0.5)
        
        # Boost if industry matches category
        if category.lower() in candidate.get("industry", "").lower():
            relevance_score += 0.3
        
        # Boost if geo matches
        if geography.lower() in candidate.get("geo", "").lower():
            relevance_score += 0.2
        
        candidate["relevance_score"] = min(relevance_score, 1.0)
    
    # Sort by relevance_score descending
    candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
    return candidates


def rank_venues(candidates: List[Dict[str, Any]], expected_attendance: int, budget_usd: int) -> List[Dict[str, Any]]:
    """
    Rank venues based on capacity fit, budget, and past events.
    """
    for candidate in candidates:
        capacity = candidate.get("capacity", 0)
        day_rate = candidate.get("day_rate_usd", 0)
        past_events = candidate.get("past_tech_events", 0)
        
        # Capacity fit score (0-1)
        if capacity >= expected_attendance * 1.2:
            capacity_score = 1.0
        elif capacity >= expected_attendance:
            capacity_score = 0.8
        else:
            capacity_score = 0.5
        
        # Budget fit score (0-1)
        if day_rate <= budget_usd:
            budget_score = 1.0
        elif day_rate <= budget_usd * 1.5:
            budget_score = 0.7
        else:
            budget_score = 0.3
        
        # Experience score (0-1)
        experience_score = min(past_events / 20.0, 1.0)
        
        relevance_score = (capacity_score * 0.4 + budget_score * 0.4 + experience_score * 0.2)
        candidate["relevance_score"] = relevance_score
    
    # Sort by relevance_score descending
    candidates.sort(key=lambda x: x["relevance_score"], reverse=True)
    return candidates