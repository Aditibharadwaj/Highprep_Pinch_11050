"""
agents/gtm_agent.py
Domain-aware GTM: conference communities, music fan platforms, sports fan channels.
"""
import json
from tools.data_loader import filter_events, get_domain
from tools.llm import call_llm

COMMUNITIES = {
    "conference": {
        "AI":          [{"name":"Hugging Face","platform":"Discord","members":"180k+"},
                        {"name":"LangChain",   "platform":"Discord","members":"70k+"},
                        {"name":"MLOps Community","platform":"Discord","members":"20k+"},
                        {"name":"AI/ML Paper Discussions","platform":"Discord","members":"50k+"}],
        "Web3":        [{"name":"Ethereum Dev","platform":"Discord","members":"200k+"},
                        {"name":"Solana",      "platform":"Discord","members":"150k+"}],
        "ClimateTech": [{"name":"MCJ Collective","platform":"Slack","members":"25k+"},
                        {"name":"Climate Draft","platform":"Discord","members":"10k+"}],
        "default":     [{"name":"Startup School","platform":"Discord","members":"60k+"},
                        {"name":"Indie Hackers", "platform":"Discord","members":"40k+"}],
    },
    "music": {
        "EDM":         [{"name":"EDC Official",   "platform":"Discord","members":"120k+"},
                        {"name":"r/EDM",          "platform":"Reddit", "members":"2M+"},
                        {"name":"Tomorrowland Community","platform":"Discord","members":"200k+"},
                        {"name":"EDM Sauce",      "platform":"Instagram","members":"500k+"}],
        "Pop/Rock":    [{"name":"r/popheads",     "platform":"Reddit","members":"1.5M+"},
                        {"name":"Coachella Fan Hub","platform":"Discord","members":"80k+"},
                        {"name":"Spotify Tastemakers","platform":"Instagram","members":"3M+"}],
        "Indie/Rock":  [{"name":"r/indieheads",   "platform":"Reddit","members":"800k+"},
                        {"name":"NH7 Weekender Community","platform":"Discord","members":"30k+"}],
        "default":     [{"name":"r/Music",        "platform":"Reddit","members":"30M+"},
                        {"name":"Bandsintown",    "platform":"App",   "members":"50M+ users"}],
    },
    "sports": {
        "Cricket":     [{"name":"r/Cricket",      "platform":"Reddit","members":"600k+"},
                        {"name":"CricBuzz Community","platform":"App", "members":"100M+"},
                        {"name":"IPL Fan Zone",   "platform":"Discord","members":"200k+"}],
        "Motorsports": [{"name":"r/formula1",     "platform":"Reddit","members":"7M+"},
                        {"name":"F1 Fan Zone",    "platform":"Discord","members":"500k+"},
                        {"name":"F1TV Community", "platform":"Discord","members":"150k+"}],
        "Football":    [{"name":"r/soccer",       "platform":"Reddit","members":"4M+"},
                        {"name":"UEFA Fan Hub",   "platform":"Discord","members":"300k+"}],
        "default":     [{"name":"ESPN Fan Network","platform":"App",  "members":"200M+"},
                        {"name":"r/sports",       "platform":"Reddit","members":"2M+"}],
    },
}

def _get_communities(domain, category):
    domain_map = COMMUNITIES.get(domain, COMMUNITIES["conference"])
    for key in domain_map:
        if key != "default" and (key.lower() in category.lower() or category.lower() in key.lower()):
            return domain_map[key]
    return domain_map.get("default", [])


def _fallback_gtm(communities, domain, category, geography, audience_size, event_name, event_date):
    """Return a complete GTM plan when LLM JSON parsing fails."""
    entity_label = {"conference": "conference", "music": "music festival", "sports": "sporting event"}.get(domain, "event")

    top_coms = []
    for c in communities[:6]:
        top_coms.append({
            "name": c["name"],
            "platform": c["platform"],
            "why": f"Active {category} community with {c.get('members','50k+')} members — high engagement and relevant audience for this {entity_label}.",
            "posting_frequency": "3x/week during launch, daily 2 weeks before event",
            "expected_reach": c.get("members", "50k+")
        })

    timeline = [
        {"week": 1, "action": "Launch event landing page, social media profiles, and email waitlist",       "channels": ["Website", "LinkedIn", "Twitter/X"],  "content_type": "Teaser Announcement"},
        {"week": 2, "action": "Open early bird ticket sales with countdown timer and referral incentive",   "channels": ["Email", "LinkedIn", "Discord"],      "content_type": "Launch Email + Social Post"},
        {"week": 3, "action": "Speaker / talent announcement series with bios and teaser content",         "channels": ["LinkedIn", "Instagram", "Twitter/X"], "content_type": "Speaker Spotlight Series"},
        {"week": 4, "action": "Community seeding: post regularly in all target communities",               "channels": ["Discord", "Reddit", "Slack"],        "content_type": "Community Post + AMA"},
        {"week": 5, "action": "Sponsor & partner announcements with co-promotion campaigns",              "channels": ["LinkedIn", "Email", "Website"],      "content_type": "Press Release + Sponsor Highlights"},
        {"week": 6, "action": "Content marketing: blog posts, podcast appearances, short-form videos",    "channels": ["Blog", "YouTube", "Instagram Reels"],"content_type": "Long-form & Short-form Content"},
        {"week": 7, "action": "FOMO campaign: limited tickets remaining, testimonials, attendee spotlights","channels": ["Email", "Instagram", "WhatsApp"],   "content_type": "Urgency & Social Proof Campaign"},
        {"week": 8, "action": "Final countdown: logistics info, last-chance tickets, hype reel release",  "channels": ["Email", "SMS", "All Social"],       "content_type": "Operational Update + Final Push"},
    ]

    hashtag_map = {
        "AI":           ["#AISummit", "#MachineLearning", "#GenAI", "#AIConference2026", "#LLMs", "#DeepLearning"],
        "Web3":         ["#Web3Summit", "#Blockchain", "#DeFi", "#CryptoConf2026", "#Decentralized", "#NFT"],
        "ClimateTech":  ["#ClimateTech", "#Sustainability", "#GreenTech", "#ClimateAction", "#NetZero2026"],
        "Music Festival":["#MusicFestival2026", "#LiveMusic", "#FestivalSeason", "#MusicLovers", "#ConcertLife"],
        "Sports":       ["#SportsBusiness", "#AthletePerformance", "#SportsEvent2026", "#GameDay", "#Champions"],
    }
    seo_map = {
        "AI":           ["AI conference 2026", "machine learning summit", "generative AI event", "LLM workshop", "AI networking"],
        "Web3":         ["blockchain conference 2026", "crypto summit", "Web3 event", "DeFi conference", "NFT summit"],
        "ClimateTech":  ["climate tech summit 2026", "green tech conference", "sustainability event", "net zero summit"],
        "Music Festival":["music festival 2026", "live music event", "outdoor festival tickets", "music concert series"],
        "Sports":       ["sports conference 2026", "athlete summit", "sports business event", "esports tournament 2026"],
    }
    hashtags    = hashtag_map.get(category, [f"#{category.replace(' ','')}", "#EventPlanning", "#Conference2026"])
    seo_keywords= seo_map.get(category, [f"{category} conference", f"{geography} event 2026", "conference registration"])

    return {
        "top_communities": top_coms,
        "gtm_timeline": timeline,
        "message_templates": {
            "discord_slack":    (
                f"\U0001f680 **{event_name}** is coming to {geography}!\n\n"
                f"Join {audience_size:,}+ {category} professionals for the premier event of 2026.\n"
                f"\U0001f3df\ufe0f Early bird tickets: [LINK] \u00b7 \U0001f4c5 {event_date}\n\n"
                "Who's attending? Drop a \U0001f525 below!"
            ),
            "linkedin_post":    (
                f"Excited to announce **{event_name}** \u2014 {geography}'s biggest {category} event of 2026!\n\n"
                f"\u2705 {audience_size:,}+ expected attendees\n"
                "\u2705 World-class speakers & hands-on workshops\n"
                "\u2705 Unmatched networking opportunities\n\n"
                f"\U0001f3df\ufe0f Grab your early bird ticket now \u2192 [LINK]\n\n"
                + " ".join(hashtags[:4])
            ),
            "email_newsletter": (
                f"Subject: You're Invited \u2014 {event_name} 2026\n\n"
                f"Dear [First Name],\n\nWe're thrilled to invite you to **{event_name}**, "
                f"taking place on {event_date} in {geography}.\n\n"
                f"This year's event brings together {audience_size:,}+ {category} professionals "
                "for inspiring keynotes, workshops, and world-class networking.\n\n"
                "\U0001f3df\ufe0f EARLY BIRD PRICING ENDS SOON\n"
                "Secure your spot: [REGISTRATION LINK]\n\n"
                f"Best,\nThe {event_name} Team"
            ),
        },
        "partnership_opportunities": [
            {"partner": f"Top {category} Media Publisher",   "type": "Media Partner",      "value_exchange": "Free press coverage & newsletter mention in exchange for complimentary media passes and banner placement."},
            {"partner": "Leading Industry Association",      "type": "Association Partner", "value_exchange": "Joint email campaigns to their member database in exchange for co-branding rights and speaking slot."},
            {"partner": f"{geography} Tech / Innovation Hub","type": "Community Partner",  "value_exchange": "Access to their startup/professional network in exchange for discounted group tickets and logo placement."},
        ],
        "hashtags":      hashtags,
        "seo_keywords":  seo_keywords,
        "content_pillars": [f"{category} Trends 2026", "Event Announcements", "Speaker Spotlights", "Behind the Scenes", "Attendee Stories"],
    }

def run(all_events, category, geography, audience_size, event_name="New Event", event_date="TBD", memory=None):
    domain      = get_domain(category)
    communities = _get_communities(domain, category)
    relevant    = filter_events(all_events, category=category, geography=geography)
    if not relevant:
        relevant = filter_events(all_events, domain=domain)

    entity_label = {"conference":"conference","music":"music festival","sports":"sporting event"}.get(domain,"event")

    context = {
        "event_name":         event_name,
        "event_type":         entity_label,
        "category":           category,
        "geography":          geography,
        "audience_size":      audience_size,
        "event_date":         event_date,
        "available_communities": communities,
        "similar_events_found":  len(relevant),
    }

    prompt = f"""You are a B2B/B2C growth marketer specializing in {entity_label} GTM strategy.

Context:
{json.dumps(context, indent=2)}

Tasks:
1. Recommend top 6 communities from the list for this {entity_label} (explain why each).
2. Create an 8-week GTM timeline tailored to a {entity_label}.
3. Write 3 message templates: Discord/Reddit, Instagram/LinkedIn post, Email newsletter.
4. Identify 3 partnership/co-promotion opportunities.
5. Suggest hashtags and SEO keywords specific to {category}.

Respond ONLY in JSON:
{{
  "top_communities": [
    {{"name":"...","platform":"...","why":"...","posting_frequency":"...","expected_reach":"..."}}
  ],
  "gtm_timeline": [
    {{"week":1,"action":"...","channels":["..."],"content_type":"..."}}
  ],
  "message_templates": {{
    "discord_slack":     "...",
    "linkedin_post":     "...",
    "email_newsletter":  "..."
  }},
  "partnership_opportunities": [
    {{"partner":"...","type":"...","value_exchange":"..."}}
  ],
  "hashtags":      ["..."],
  "seo_keywords":  ["..."],
  "content_pillars": ["..."]
}}"""

    raw = call_llm(prompt)
    raw = raw.replace("```json","").replace("```","").strip()
    try:
        result = json.loads(raw)
        if not result.get("top_communities") or not result.get("gtm_timeline"):
            raise ValueError("Missing required GTM keys")
    except Exception:
        # Fallback: generate complete GTM plan so tab never shows empty
        result = _fallback_gtm(communities, domain, category, geography, audience_size, event_name, event_date)

    result["community_database_used"] = communities
    result["domain"]                  = domain
    return result