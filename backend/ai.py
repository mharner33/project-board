import json
import logging
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from models import AIResponse, BoardOut

logger = logging.getLogger(__name__)

load_dotenv()

MODEL = "openai/gpt-oss-120b"

_client: OpenAI | None = None


def get_ai_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
        )
    return _client


def simple_chat(prompt: str) -> str:
    client = get_ai_client()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


SYSTEM_PROMPT = """\
You are an AI assistant for a Kanban board app called Kanban Studio. \
The user will ask you questions or give you instructions about their board.

You MUST respond with valid JSON matching this exact schema:
{
  "message": "Your text response to the user",
  "board_updates": []
}

board_updates is an array of operations. Each operation is one of:

1. Create a card:
   {"action": "create_card", "column_id": <int>, "title": "<string>", "details": "<string>"}

2. Update a card:
   {"action": "update_card", "card_id": <int>, "title": "<string or null>", "details": "<string or null>"}

3. Move a card:
   {"action": "move_card", "card_id": <int>, "target_column_id": <int>, "position": <int>}

4. Delete a card:
   {"action": "delete_card", "card_id": <int>}

Rules:
- Use the column and card IDs from the board state provided below.
- position is 0-based (0 = top of column).
- Only include board_updates if the user asks you to change the board.
- For normal conversation, return an empty board_updates array.
- Always include a helpful message.
- Respond ONLY with the JSON object, no markdown fences or extra text.

Current board state:
"""


def board_to_context(board: BoardOut) -> str:
    data = {
        "columns": [
            {
                "id": col.id,
                "title": col.title,
                "cards": [
                    {"id": c.id, "title": c.title, "details": c.details}
                    for c in col.cards
                ],
            }
            for col in board.columns
        ]
    }
    return json.dumps(data, indent=2)


def chat_with_board(
    board: BoardOut,
    user_message: str,
    history: list[dict[str, str]],
) -> AIResponse:
    client = get_ai_client()

    system_content = SYSTEM_PROMPT + board_to_context(board)
    messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    return _parse_ai_response(raw)


def _parse_ai_response(raw: str) -> AIResponse:
    try:
        return AIResponse.model_validate_json(raw)
    except Exception:
        pass

    # Try extracting JSON from markdown fences or surrounding text
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        try:
            return AIResponse.model_validate_json(match.group())
        except Exception:
            pass

    # Last resort: treat entire raw text as a plain message
    logger.warning("Could not parse AI response as JSON, returning raw text as message")
    text = raw.strip() or "I couldn't process that request. Please try again."
    return AIResponse(message=text, board_updates=[])
