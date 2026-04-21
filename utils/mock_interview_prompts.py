import json


def build_interview_system_prompt(target_field: str, max_rounds: int) -> str:
    field = (target_field or "General").strip()
    total_rounds = 3
    return (
        "You are an expert mock interviewer. "
        f"The user is preparing for interviews in: {field}. "
        "You must conduct a realistic interview and follow these rules:\n"
        "1) Ask one question at a time.\n"
        "2) Keep tone professional and concise.\n"
        "3) Ask exactly 3 questions total.\n"
        "4) Do not provide feedback before all 3 answers are received.\n"
        "5) For rounds 1 and 2, set feedback='' and closing_message=''.\n"
        "6) For round 3 completion, set should_end=true and next_question=''.\n"
        "5) If user says they want to end, finish early.\n"
        f"7) Keep the interview to exactly {total_rounds} answer rounds unless user ends early.\n"
        "8) Always return strict JSON with keys: feedback, next_question, should_end, closing_message.\n"
        "9) do not include markdown fences."
    )


def build_turn_user_prompt(conversation_text: str, rounds_done: int, max_rounds: int) -> str:
    total_rounds = 3
    return (
        "Use the conversation transcript to decide the next interviewer turn.\n"
        f"Rounds done by candidate: {rounds_done}/{total_rounds}.\n"
        "If rounds_done < 3: ask only the next single question, feedback must be ''.\n"
        "If rounds_done >= 3: set should_end=true and next_question=''.\n"
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
