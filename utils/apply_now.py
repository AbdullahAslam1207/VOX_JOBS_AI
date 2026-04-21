import os
import re
import logging
from typing import List, Set, Optional

import httpx

logger = logging.getLogger(__name__)

DUMMY_APPLY_API_URL = "https://21g0pfhj-8000.inc1.devtunnels.ms/apply/run"


def _extract_job_url(job: dict) -> str:
    """Extract canonical job URL from a job card."""
    return (
        job.get("url")
        or job.get("job_url")
        or job.get("job_link")
        or job.get("apply_url")
        or job.get("link")
        or ""
    ).strip()


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


async def trigger_dummy_apply_api(job_cards: List[dict], session_id: str, email: str):
    """Fire-and-forget apply calls to /apply/run with email + job url."""
    if not email:
        logger.warning("Apply API skipped for session %s: missing email", session_id)
        return

    payloads = []
    seen_urls = set()
    for card in job_cards:
        url = _extract_job_url(card)
        if url and url not in seen_urls:
            seen_urls.add(url)
            payloads.append({"email": email, "url": url})

    if not payloads:
        logger.warning("Apply API skipped for session %s: no valid job urls", session_id)
        return

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            for payload in payloads:
                response = await client.post(DUMMY_APPLY_API_URL, json=payload)
                response.raise_for_status()
        logger.info("Apply API called successfully for session %s (%d jobs)", session_id, len(payloads))
    except Exception as error:
        logger.error("Apply API call failed for session %s: %s", session_id, str(error))


def process_dummy_apply(email: Optional[str], url: Optional[str]):
    """Simulate /apply/run background processing."""
    import time

    time.sleep(1)
    logger.info("Dummy apply completed for email=%s, url=%s", email or "", url or "")
