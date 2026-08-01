"""
Google Maps Places API tool — searches for local businesses by type and location.
Docs: https://developers.google.com/maps/documentation/places/web-service
"""
import asyncio
import logging
import certifi
import httpx
from core.context import get_key

logger = logging.getLogger(__name__)

PLACES_BASE = "https://maps.googleapis.com/maps/api/place"


async def search_local_businesses(
    query: str,
    location: str | None = None,
    radius_meters: int = 50000,
    max_results: int = 20,
) -> list[dict]:
    """
    Search Google Maps Places for local businesses matching the query.
    Returns list of business dicts with name, address, rating, reviews, website, phone.
    Paginates up to 3 pages (60 results max) and filters permanently-closed listings.
    """
    api_key = get_key("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_MAPS_API_KEY not set — returning empty results (no mock)")
        return []

    search_query = f"{query} {location}".strip() if location else query
    logger.info("Google Maps search: query='%s'", search_query)

    raw_places: list[dict] = []
    async with httpx.AsyncClient(timeout=15.0, verify=certifi.where()) as client:
        # radius is only meaningful alongside an explicit lat/lng location.
        # For plain text queries like "HVAC contractors Kentucky", omitting radius
        # lets the Places Text Search engine use its own geographic ranking.
        params: dict = {"query": search_query, "key": api_key}
        # Paginate up to 3 pages (20 results each = 60 max)
        for page in range(3):
            response = await client.get(f"{PLACES_BASE}/textsearch/json", params=params)
            response.raise_for_status()
            data = response.json()
            api_status = data.get("status", "UNKNOWN")
            page_results = data.get("results", [])
            if api_status not in ("OK", "ZERO_RESULTS"):
                logger.warning(
                    "Google Maps API status='%s' error='%s' for query='%s'",
                    api_status, data.get("error_message", ""), search_query,
                )
            logger.info(
                "Google Maps page %d: status=%s raw=%d for query='%s'",
                page + 1, api_status, len(page_results), search_query,
            )
            # Filter permanently closed before adding
            open_results = [
                p for p in page_results
                if p.get("business_status") != "PERMANENTLY_CLOSED"
            ]
            raw_places.extend(open_results)
            next_token = data.get("next_page_token")
            if not next_token or len(raw_places) >= max_results:
                break
            # Google requires a short delay before next_page_token becomes valid
            await asyncio.sleep(2)
            params = {"key": api_key, "pagetoken": next_token}

    places = raw_places[:max_results]
    logger.info("Google Maps: %d open places after pagination", len(places))

    # Parse all places, then fetch missing contact details in parallel
    businesses = [_parse_place(p) for p in places]

    async def _maybe_details(i: int) -> dict:
        if not businesses[i]["website"] or not businesses[i]["phone"]:
            return await _fetch_place_details(places[i].get("place_id", ""), api_key)
        return {}

    details_list = await asyncio.gather(
        *[_maybe_details(i) for i in range(len(businesses))],
        return_exceptions=True,
    )

    results = []
    for business, details in zip(businesses, details_list):
        if isinstance(details, dict):
            business["website"] = details.get("website") or business["website"]
            business["phone"] = details.get("formatted_phone_number") or business["phone"]
        business["local_score"] = _score_local(business)
        results.append(business)

    results.sort(key=lambda x: x["local_score"], reverse=True)
    return results


async def _fetch_place_details(place_id: str, api_key: str) -> dict:
    if not place_id:
        return {}
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=certifi.where()) as client:
            response = await client.get(
                f"{PLACES_BASE}/details/json",
                params={
                    "place_id": place_id,
                    "fields": "website,formatted_phone_number",
                    "key": api_key,
                },
            )
            response.raise_for_status()
            return response.json().get("result", {})
    except Exception as e:
        logger.warning(f"Place details fetch failed for {place_id}: {e}")
        return {}


def _parse_place(place: dict) -> dict:
    geometry = place.get("geometry", {}).get("location", {})
    return {
        "id": place.get("place_id", ""),
        "name": place.get("name", ""),
        "address": place.get("formatted_address", ""),
        "rating": place.get("rating"),
        "review_count": place.get("user_ratings_total", 0),
        "website": place.get("website", ""),
        "phone": place.get("formatted_phone_number", ""),
        "lat": geometry.get("lat"),
        "lng": geometry.get("lng"),
        "types": place.get("types", []),
        "business_status": place.get("business_status", ""),
        "source": "google_maps",
    }


def _score_local(business: dict) -> int:
    """
    Score a local business lead out of 100:
      rating   → 40 pts  (Google rating 0-5 scaled linearly)
      reviews  → 25 pts  (tiered: 100+ → 25, 50+ → 18, 10+ → 10, else 0)
      website  → 20 pts  (binary)
      phone    → 15 pts  (binary)
    """
    score = 0

    # Rating (40 pts)
    rating = business.get("rating")
    if rating is not None:
        score += round((float(rating) / 5.0) * 40)

    # Reviews (25 pts) — give 5 pts for any reviews so rural/new businesses aren't zero'd out
    reviews = business.get("review_count", 0) or 0
    if reviews >= 100:
        score += 25
    elif reviews >= 50:
        score += 18
    elif reviews >= 10:
        score += 10
    elif reviews >= 1:
        score += 5

    # Website (20 pts)
    if business.get("website"):
        score += 20

    # Phone (15 pts)
    if business.get("phone"):
        score += 15

    return score


