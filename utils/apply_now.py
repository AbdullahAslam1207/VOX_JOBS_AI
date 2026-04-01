import os
import re
import logging
from typing import List, Set

import httpx

logger = logging.getLogger(__name__)

DUMMY_APPLY_API_URL = os.getenv("DUMMY_APPLY_API_URL", "http://127.0.0.1:8000/dummy_apply_jobs")


def _extract_apply_indices(query: str, total_jobs: int) -> Set[int]:
    """Extract 0-based job indices from apply command text."""
    lowered = query.lower()
    indices: Set[int] = set()

    if "all" in lowered:
        return set(range(total_jobs))

    ordinal_map = {
        "first": 1,
        "1st": 1,
        "one": 1,
        "second": 2,
        "2nd": 2,
        "two": 2,
        "third": 3,
        "3rd": 3,
        "three": 3,
        "fourth": 4,
        "4th": 4,
        "four": 4,
        "fifth": 5,
        "5th": 5,
        "five": 5,
    }

    for token, position in ordinal_map.items():
        if f" {token} " in f" {lowered} ":
            index = position - 1
            if 0 <= index < total_jobs:
                indices.add(index)

    for match in re.findall(r"\b(\d+)(?:st|nd|rd|th)?\b", lowered):
        number = int(match)
        if 1 <= number <= total_jobs:
            indices.add(number - 1)

    return indices


def resolve_apply_action(query: str, known_jobs: List[dict]) -> dict:
    """
    Resolve whether the query is an apply command and selected cards.

    Returns:
        {
            "is_apply_intent": bool,
            "check": bool,
            "jobs": list
        }
    """
    lowered = query.lower().strip()
    is_apply_intent = any(keyword in lowered for keyword in ["apply", "submit application", "send application"])

    if not is_apply_intent:
        return {"is_apply_intent": False, "check": False, "jobs": []}

    if not known_jobs:
        return {"is_apply_intent": True, "check": False, "jobs": []}

    indices = _extract_apply_indices(lowered, len(known_jobs))
    selected_jobs = [known_jobs[i] for i in sorted(indices)] if indices else []

    return {
        "is_apply_intent": True,
        "check": len(selected_jobs) > 0,
        "jobs": selected_jobs,
    }


async def trigger_dummy_apply_api(job_cards: List[dict], session_id: str):
    """Fire-and-forget apply call to dummy API."""
    payload = {
        "session_id": session_id,
        "job_cards": job_cards,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(DUMMY_APPLY_API_URL, json=payload)
            response.raise_for_status()
        logger.info("Dummy apply API called successfully for %d jobs", len(job_cards))
    except Exception as error:
        logger.error("Dummy apply API call failed: %s", str(error))


def process_dummy_apply(job_cards: List[dict], session_id: str):
    """Simulate dummy apply processing in background."""
    import time

    time.sleep(2)
    logger.info("Dummy apply completed for session %s, jobs count: %d", session_id, len(job_cards))
