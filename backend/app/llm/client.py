from openai import APIError, OpenAI

from app.config import get_settings

settings = get_settings()

# every LLM call in this system goes through here, and every one of them is optional.
# if there's no API key configured, callers fall back to rule-based logic instead of crashing.
# that matters for a reviewer who clones the repo without a key: the reasoning core still runs.
# Groq implements the OpenAI Chat Completions API, so the openai SDK works unchanged against it -
# only the base_url, api_key, and model name point at Groq instead.

_client: OpenAI | None = None


def is_available() -> bool:
    return bool(settings.groq_api_key)


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)
    return _client


def complete(system_prompt: str, user_prompt: str, temperature: float = 0.3, json_mode: bool = False) -> str | None:
    if not is_available():
        return None
    try:
        response = get_client().chat.completions.create(
            model=settings.groq_model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"} if json_mode else None,
        )
        return response.choices[0].message.content
    except APIError:
        # a flaky LLM call should degrade to the rule-based path, never take the whole request down
        return None
