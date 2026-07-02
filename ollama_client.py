import os
import re
import requests

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3:1.7b"

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"


def clean_model_response(response_text: str) -> str:
    if not response_text:
        return ""

    response_text = re.sub(
        r"<think>.*?</think>",
        "",
        response_text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    return response_text.strip()


def _get_groq_api_key() -> str:
    try:
        import streamlit as st

        return st.secrets.get("GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    except Exception:
        return os.getenv("GROQ_API_KEY", "")


def check_groq_ready() -> bool:
    return bool(_get_groq_api_key())


def _cloud_backend_not_configured_message() -> str:
    return (
        "### Cloud model backend is not configured\n\n"
        "Voreenth successfully inspected and approved this prompt, but the hosted "
        "Groq Cloud backend is not configured yet.\n\n"
        "To enable live model responses on Streamlit Cloud, add `GROQ_API_KEY` "
        "to Streamlit secrets.\n\n"
        "The runtime security workflow still executed successfully:\n\n"
        "- Prompt inspection completed\n"
        "- Risk scoring completed\n"
        "- Policy enforcement completed\n"
        "- Request telemetry was logged"
    )


def _cloud_backend_rate_limit_message() -> str:
    return (
        "## ⚠️ Groq Cloud Rate Limit Reached\n\n"
        "Groq Cloud is temporarily unavailable or has reached its current rate limit.\n\n"
        "Voreenth successfully completed:\n\n"
        "✅ Runtime Prompt Inspection\n"
        "✅ Risk Scoring\n"
        "✅ Policy Enforcement\n"
        "✅ SQLite Telemetry Logging\n\n"
        "Please try again later, switch to **Demo Mode**, or run Voreenth locally using "
        "**Local Ollama**."
    )


def _cloud_backend_timeout_message() -> str:
    return (
        "## ⚠️ Cloud Backend Timeout\n\n"
        "The Groq Cloud backend did not respond within the expected time.\n\n"
        "Voreenth successfully completed all runtime security inspection and policy "
        "enforcement before the model request.\n\n"
        "Please retry shortly or switch to **Demo Mode**."
    )


def _cloud_backend_unavailable_message() -> str:
    return (
        "## ⚠️ Cloud Backend Unavailable\n\n"
        "The hosted Groq backend is currently unavailable.\n\n"
        "Voreenth successfully completed runtime inspection, risk scoring, policy "
        "enforcement, and telemetry logging.\n\n"
        "Please retry later, use **Demo Mode**, or run Voreenth locally with "
        "**Local Ollama**."
    )


def ask_groq(prompt: str, model_name: str = DEFAULT_GROQ_MODEL) -> str:
    api_key = _get_groq_api_key()

    if not api_key:
        return _cloud_backend_not_configured_message()

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a concise enterprise AI assistant. "
                    "Respond in clean Markdown. "
                    "Use short paragraphs and bullets. "
                    "Do not expose reasoning. "
                    "Keep responses demo-friendly and under 300 words unless asked otherwise."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "max_tokens": 350,
    }

    try:
        response = requests.post(
            GROQ_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )

        if response.status_code == 429:
            return _cloud_backend_rate_limit_message()

        response.raise_for_status()
        data = response.json()

        raw_response = data["choices"][0]["message"]["content"]
        return clean_model_response(raw_response)

    except requests.Timeout:
        return _cloud_backend_timeout_message()

    except requests.RequestException:
        return _cloud_backend_unavailable_message()

    except (KeyError, IndexError, TypeError, ValueError):
        return (
            "## ⚠️ Cloud Backend Response Error\n\n"
            "The hosted model returned an unexpected response format.\n\n"
            "Voreenth still completed prompt inspection, risk scoring, policy enforcement, "
            "and telemetry logging.\n\n"
            "Please retry later or switch to **Demo Mode**."
        )


def ask_ollama(prompt: str, model_name: str = DEFAULT_MODEL) -> str:
    payload = {
        "model": model_name,
        "prompt": prompt,
        "system": (
            "You are a concise enterprise AI assistant. "
            "Respond in clean Markdown. "
            "Use short paragraphs and bullets. "
            "Do not expose reasoning. "
            "Do not use <think> tags. "
            "Keep responses demo-friendly and under 300 words unless asked otherwise."
        ),
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "num_predict": 350,
        },
    }

    response = requests.post(
        OLLAMA_ENDPOINT,
        json=payload,
        timeout=180,
    )

    response.raise_for_status()
    data = response.json()

    raw_response = data.get("response", "")
    return clean_model_response(raw_response)


def ask_demo(prompt: str) -> str:
    return (
        "### Demo Mode Response\n\n"
        "Voreenth successfully inspected this prompt and allowed it through the runtime "
        "security gateway.\n\n"
        "In a production deployment, this approved request would be forwarded to the "
        "configured enterprise model backend, such as Groq, Azure OpenAI, Amazon Bedrock, "
        "Google Vertex AI, Anthropic Claude, or a self-hosted model.\n\n"
        "This demo response confirms the security workflow executed successfully:\n\n"
        "- Prompt inspection completed\n"
        "- Risk scoring completed\n"
        "- Policy decision returned `ALLOW`\n"
        "- Telemetry logged to SQLite"
    )


def ask_llm(prompt: str, backend: str, model_name: str) -> str:
    if backend == "Groq Cloud":
        return ask_groq(prompt, model_name=model_name)

    if backend == "Local Ollama":
        return ask_ollama(prompt, model_name=model_name)

    return ask_demo(prompt)


def check_ollama_health() -> bool:
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False
