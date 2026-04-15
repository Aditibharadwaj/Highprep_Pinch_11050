"""
tools/web_scraper.py
Lightweight web data aggregation for sponsors, speakers, and events.
"""
import requests
from bs4 import BeautifulSoup
import time


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _safe_get(url: str, timeout: int = 8) -> requests.Response | None:
    """Safe HTTP GET with timeout and error handling."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp
    except Exception as e:
        print(f"[Scraper] Failed to fetch {url}: {e}")
        return None


def scrape_eventbrite_events(query: str, location: str = "") -> list[dict]:
    """
    Search Eventbrite for events matching query + location.
    Returns list of event dicts with name, date, location, url.
    """
    search_url = (
        f"https://www.eventbrite.com/d/{location.lower().replace(' ', '-')}/"
        f"{query.lower().replace(' ', '-')}/"
    )

    resp = _safe_get(search_url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    for card in soup.select("div[data-testid='event-card']")[:10]:
        try:
            name = card.select_one("h2").get_text(strip=True) if card.select_one("h2") else ""
            date = card.select_one("p[data-testid='event-card-date']")
            date = date.get_text(strip=True) if date else ""
            loc = card.select_one("p[data-testid='event-card-location']")
            loc = loc.get_text(strip=True) if loc else ""
            link = card.select_one("a")
            url = link["href"] if link else ""

            if name:
                events.append({
                    "Event Name": name,
                    "Date": date,
                    "Location": loc,
                    "URL": url,
                    "Source": "Eventbrite"
                })
        except Exception:
            continue

    print(f"[Scraper] Eventbrite: found {len(events)} events for '{query}'")
    return events


def scrape_luma_events(query: str) -> list[dict]:
    """
    Search lu.ma for tech events.
    Returns list of event dicts.
    """
    url = f"https://lu.ma/search?q={query.replace(' ', '+')}"
    resp = _safe_get(url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    for card in soup.select("a.event-link")[:10]:
        try:
            name = card.get_text(strip=True)
            href = card.get("href", "")
            if name:
                events.append({
                    "Event Name": name,
                    "URL": f"https://lu.ma{href}" if href.startswith("/") else href,
                    "Source": "Luma"
                })
        except Exception:
            continue

    print(f"[Scraper] Luma: found {len(events)} events for '{query}'")
    return events


def search_sponsors_web(category: str, geography: str) -> list[str]:
    """
    Use a simple Google search scrape to find potential sponsors.
    Returns list of company/sponsor names.
    """
    query = f"{category} conference sponsors {geography} 2025 site:linkedin.com OR site:techcrunch.com"
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=10"

    resp = _safe_get(url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    names = []

    for result in soup.select("h3")[:10]:
        text = result.get_text(strip=True)
        if text and len(text) > 3:
            names.append(text)

    return names[:10]


def scrape_conference_speakers(event_url: str) -> list[str]:
    """
    Scrape speaker names from a conference website URL.
    Returns list of speaker names.
    """
    resp = _safe_get(event_url)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    speakers = []

    # Common patterns for speaker sections
    for tag in soup.select("h3, h4, .speaker-name, [class*='speaker']"):
        text = tag.get_text(strip=True)
        if text and 3 < len(text) < 60:  # reasonable name length
            speakers.append(text)

    # Deduplicate
    seen = set()
    unique = []
    for s in speakers:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    print(f"[Scraper] Found {len(unique)} speakers at {event_url}")
    return unique[:20]


def aggregate_event_data(category: str, geography: str) -> list[dict]:
    """
    ✅ Main aggregation function called by agents.
    Combines Eventbrite + Luma results into a unified list.
    """
    print(f"[Scraper] Aggregating live data: {category} / {geography}")

    results = []

    # Eventbrite
    eb_events = scrape_eventbrite_events(f"{category} conference", geography)
    results.extend(eb_events)

    # Small delay to be respectful
    time.sleep(1)

    # Luma
    luma_events = scrape_luma_events(f"{category} {geography}")
    results.extend(luma_events)

    return results