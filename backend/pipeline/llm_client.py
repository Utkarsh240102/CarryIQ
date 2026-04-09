"""
LLM Client Setup (Substep 3.1)
--------------------------------
Central connection manager for the AI language model.
Supports two providers via the OpenAI-compatible Python SDK:
  - OpenRouter  (LLM_PROVIDER=openrouter)
  - Groq        (LLM_PROVIDER=groq)

All other Step 3 files import `get_llm_client()` and `chat()` from here.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ─── Load environment variables from project root .env ───────────────────────

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)

# ─── Provider configuration ───────────────────────────────────────────────────

PROVIDER_CONFIGS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_env": "OPENROUTER_API_KEY",
        "default_model": "openai/gpt-4o-mini",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "default_model": "llama-3.1-70b-versatile",
    },
}


# ─── Core functions ───────────────────────────────────────────────────────────

def get_llm_client() -> tuple[OpenAI, str]:
    """
    Read LLM_PROVIDER from .env, build and return an OpenAI-compatible client.

    Returns:
        (client, model_name)  — ready to use in any chat call.

    Raises:
        ValueError: If provider is unsupported or API key is missing.
    """
    provider = os.getenv("LLM_PROVIDER", "openrouter").lower()

    if provider not in PROVIDER_CONFIGS:
        raise ValueError(
            f"Unsupported LLM_PROVIDER='{provider}'. "
            f"Choose from: {list(PROVIDER_CONFIGS.keys())}"
        )

    config = PROVIDER_CONFIGS[provider]
    api_key = os.getenv(config["api_key_env"], "")

    if not api_key or api_key == "your_openrouter_key_here" or api_key == "your_groq_key_here":
        raise ValueError(
            f"API key for provider '{provider}' is missing or not set.\n"
            f"Please set {config['api_key_env']} in your .env file."
        )

    # Model: prefer env override, fall back to provider default
    model = os.getenv("LLM_MODEL", config["default_model"])

    client = OpenAI(
        api_key=api_key,
        base_url=config["base_url"],
    )

    return client, model


def chat(
    prompt: str,
    system: str = "You are a helpful data analysis assistant.",
    temperature: float = 0.2,
    max_tokens: int = 1500,
) -> str:
    """
    Send a single prompt to the configured LLM and return the response text.

    Args:
        prompt      : The user message / question to send.
        system      : The system instruction that sets the AI's role.
        temperature : Controls randomness. Lower = more consistent output.
        max_tokens  : Maximum length of the AI's response.

    Returns:
        The AI's response as a plain string.

    Raises:
        RuntimeError: If the API call fails for any reason.
    """
    client, model = get_llm_client()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        raise RuntimeError(f"LLM API call failed: {e}") from e


def check_connection() -> bool:
    """
    Quick health check — sends a tiny test message to verify the LLM works.

    Returns:
        True if connection is healthy, False otherwise.
    """
    try:
        reply = chat(
            prompt="Reply with exactly: OK",
            max_tokens=10,
        )
        success = "ok" in reply.lower()
        if success:
            print("[LLM] Connection check: PASSED")
        else:
            print(f"[LLM] Connection check: unexpected reply -> '{reply}'")
        return success
    except (RuntimeError, ValueError) as e:
        print(f"[LLM] Connection check: FAILED ({e})")
        return False


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Testing LLM connection...")
    ok = check_connection()
    if not ok:
        print("\nHint: Make sure your .env file has a valid API key.")
