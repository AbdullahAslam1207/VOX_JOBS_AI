import json


def build_interview_system_prompt(target_field: str, max_rounds: int) -> str:
    field = (target_field or "General").strip()
    return (
        "You are an expert mock interviewer. "
        f"The user is preparing for interviews in: {field}. "
        "You must conduct a realistic interview and follow these rules:\n"
        "1) Ask one question at a time.\n"
        "2) Keep tone professional and concise.\n"
        "3) After each user answer, give short feedback and ask the next question.\n"
        f"4) Keep the interview to at most {max_rounds} answer rounds.\n"
        "5) If user says they want to end, finish early.\n"
        "6) Always return strict JSON with keys: feedback, next_question, should_end, closing_message.\n"
        "7) do not include markdown fences."
    )


def build_turn_user_prompt(conversation_text: str, rounds_done: int, max_rounds: int) -> str:
    return (
        "Use the conversation transcript to decide the next interviewer turn.\n"
        f"Rounds done by candidate: {rounds_done}/{max_rounds}.\n"
        "If rounds_done >= max_rounds, set should_end=true and next_question='' with a brief closing_message.\n"
        "Return strict JSON only.\n\n"
        "Transcript:\n"
        f"{conversation_text}"
    )


def build_evaluation_system_prompt(target_field: str) -> str:
    field = (target_field or "General").strip()
    return (
        "You are an interview evaluator. "
        f"Evaluate this mock interview for field: {field}. "
        "Return strict JSON with keys: score, strengths, improvements, summary.\n"
        "Rules:\n"
        "- score must be an integer from 0 to 100.\n"
        "- strengths: array of 2-4 short strings.\n"
        "- improvements: array of 2-4 short strings.\n"
        "- summary: 1-2 sentences.\n"
        "- Output only JSON without markdown fences."
    )


def build_evaluation_user_prompt(conversation_text: str) -> str:
    return "Evaluate the transcript below and return strict JSON only.\n\nTranscript:\n" + conversation_text


def parse_json_response(text: str, fallback: dict) -> dict:
    try:
        if not text:
            return fallback
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception:
        return fallback
