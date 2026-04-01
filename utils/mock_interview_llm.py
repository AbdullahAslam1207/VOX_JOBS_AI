import os
from groq import Groq

from utils.mock_interview_prompts import (
    build_interview_system_prompt,
    build_turn_user_prompt,
    build_evaluation_system_prompt,
    build_evaluation_user_prompt,
    parse_json_response,
)


class MockInterviewLLM:
    def __init__(self, model: str = "llama-3.1-8b-instant"):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        self.client = Groq(api_key=api_key)
        self.model = model

    def _chat(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4,
            stream=False,
        )
        return response.choices[0].message.content

    def opening_question(self, target_field: str) -> str:
        prompt = (
            f"Start a mock interview for {target_field}. Ask only the first interview question in one sentence."
        )
        content = self._chat(
            [
                {
                    "role": "system",
                    "content": "You are a professional interviewer. Ask one concise opening interview question.",
                },
                {"role": "user", "content": prompt},
            ]
        )
        return (content or "Tell me about yourself and your experience relevant to this role.").strip()

    def next_turn(self, target_field: str, chat_history: list, rounds_done: int, max_rounds: int) -> dict:
        transcript_lines = []
        for turn in chat_history:
            user_msg = (turn.get("userMessage") or "").strip()
            bot_msg = (turn.get("botResponse") or "").strip()
            if user_msg:
                transcript_lines.append(f"Candidate: {user_msg}")
            if bot_msg:
                transcript_lines.append(f"Interviewer: {bot_msg}")

        transcript = "\n".join(transcript_lines)
        system_prompt = build_interview_system_prompt(target_field, max_rounds)
        user_prompt = build_turn_user_prompt(transcript, rounds_done, max_rounds)

        fallback = {
            "feedback": "Thank you for your answer.",
            "next_question": "Can you share a specific project example that demonstrates your skills?",
            "should_end": rounds_done >= max_rounds,
            "closing_message": "",
        }

        content = self._chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        parsed = parse_json_response(content, fallback)

        feedback = str(parsed.get("feedback", fallback["feedback"]))
        next_question = str(parsed.get("next_question", fallback["next_question"]))
        closing_message = str(parsed.get("closing_message", ""))
        should_end = bool(parsed.get("should_end", fallback["should_end"]))

        if rounds_done >= max_rounds:
            should_end = True
            next_question = ""

        return {
            "feedback": feedback.strip(),
            "next_question": next_question.strip(),
            "should_end": should_end,
            "closing_message": closing_message.strip(),
        }

    def evaluate(self, target_field: str, chat_history: list) -> dict:
        transcript_lines = []
        for turn in chat_history:
            user_msg = (turn.get("userMessage") or "").strip()
            bot_msg = (turn.get("botResponse") or "").strip()
            if user_msg:
                transcript_lines.append(f"Candidate: {user_msg}")
            if bot_msg:
                transcript_lines.append(f"Interviewer: {bot_msg}")

        transcript = "\n".join(transcript_lines)

        fallback = {
            "score": 70,
            "strengths": ["Clear communication", "Relevant examples"],
            "improvements": ["Add more measurable outcomes", "Structure answers with STAR"],
            "summary": "Good baseline preparation with room to improve answer depth and structure.",
        }

        content = self._chat(
            [
                {"role": "system", "content": build_evaluation_system_prompt(target_field)},
                {"role": "user", "content": build_evaluation_user_prompt(transcript)},
            ]
        )
        parsed = parse_json_response(content, fallback)

        try:
            score = int(parsed.get("score", fallback["score"]))
        except Exception:
            score = fallback["score"]
        score = max(0, min(score, 100))

        strengths = parsed.get("strengths", fallback["strengths"])
        improvements = parsed.get("improvements", fallback["improvements"])
        summary = str(parsed.get("summary", fallback["summary"]))

        if not isinstance(strengths, list) or not strengths:
            strengths = fallback["strengths"]
        if not isinstance(improvements, list) or not improvements:
            improvements = fallback["improvements"]

        return {
            "score": score,
            "strengths": [str(item) for item in strengths[:4]],
            "improvements": [str(item) for item in improvements[:4]],
            "summary": summary.strip(),
        }


_interview_llm = None


def get_mock_interview_llm() -> MockInterviewLLM:
    global _interview_llm
    if _interview_llm is None:
        _interview_llm = MockInterviewLLM()
    return _interview_llm
