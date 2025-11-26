
import re
import json


def build_chat_prompt(data):
    try:
        print(data)
        result = "[\n"
        for i, item in enumerate(data, start=1):
            # Escape single { and } by doubling them
            user_message = item["userMessage"].replace("{", "{{").replace("}", "}}")
            bot_response = item["botResponse"].replace("{", "{{").replace("}", "}}")

            # Build the labeled block
            result += f'    "Response {i}": {{' + "{\n"
            result += f'        "userMessage": "{user_message}",\n'
            result += f'        "botResponse": "{bot_response}"\n'
            result += "    }}"  # <-- only close, no comma here

            # Add a comma only if it’s not the last item
            if i != len(data):
                result += ",\n\n"
            else:
                result += "\n"

        result += "]"
        return result
    except Exception as e:
        print(f'the issue is in build chat prompt {str(e)}')


def clean_and_parse(raw):
    """
    Cleans and parses raw card JSON text.
    - Removes ```json, ``` and trailing ...
    - Handles both single {} and list [] JSON formats
    - Wraps single dicts in a list for consistency
    """
    try:
        cleaned = (
            raw.replace("```json", "")
            .replace("```", "")
            .strip()
        )

        if cleaned.startswith("{") and cleaned.endswith("}"):
            # Step 1: Remove markdown/code block markers and trailing dots
            cleaned = re.sub(r'\.*$', '', cleaned).strip()  # remove trailing ...
            cleaned = f"[{cleaned}]"
            return cleaned
        else:
            return raw
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return None
