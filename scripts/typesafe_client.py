"""
TypeSafe Jev HTTP API client — thin abstraction layer.

To switch to the Python SDK later, replace the body of `call_api` only.
The function signature stays the same so nothing else in the codebase changes.

API reference: https://docs.typesafe.ai/api.md
"""

import requests

# Override with TYPESAFE_API_URL environment variable if needed.
# Verify current endpoint at: https://docs.typesafe.ai/api.md
DEFAULT_API_URL = "https://api.typesafe.ai/v1/systemone"


def call_api(state, questions, model, api_key, api_url=None):
    """
    Call the TypeSafe System One API.

    Args:
        state:     dict  — context object for all questions in this call
        questions: dict  — map of question_id -> question definition
        model:     str   — model identifier, e.g. "jev-1.13.0"
        api_key:   str   — TypeSafe API key
        api_url:   str | None — override API endpoint (defaults to DEFAULT_API_URL)

    Returns:
        dict — full API response, including "answers" key

    Raises:
        requests.HTTPError  — on non-2xx HTTP response
        requests.Timeout    — if request exceeds timeout
    """
    url = api_url or DEFAULT_API_URL
    payload = {
        "model": model,
        "state": state,
        "questions": questions,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()
