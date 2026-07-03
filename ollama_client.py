import os
import re
import requests


BACKEND_CLOUD = "cloud"
BACKEND_LOCAL = "local_ollama"
BACKEND_SIMULATION = "simulation"

BACKEND_OPTIONS = {
    "☁️ Cloud LLM": BACKEND_CLOUD,
    "💻 Local Ollama": BACKEND_LOCAL,
    "🎭 Simulation Mode": BACKEND_SIMULATION,
}

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
DEFAULT_LOCAL_MODEL = "qwen3:1.7b"
DEFAULT_MODEL = DEFAULT_LOCAL_MODEL

CLOUD_LLM_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_CLOUD_MODEL = "llama-3.1-8b-instant"
DEFAULT_GROQ_MODEL = DEFAULT_CLOUD_MODEL


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


def _get_cloud_api_key() -> str:
    try:
        import streamlit as st
        return st.secrets.get("GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    except Exception:
        return os.getenv("GROQ_API_KEY", "")


def check_cloud_ready() -> bool:
    return bool(_get_cloud_api_key())


def check_groq_ready() -> bool:
    return check_cloud_ready()


def _not_configured_message() -> str:
    return (
        "### Cloud LLM is not configured\n\n"
        "Voreenth successfully inspected and approved this prompt, but the hosted "
        "cloud model backend is not configured.\n\n"
        "The runtime security workflow still executed successfully:\n\n"
        "- Prompt inspection completed\n"
        "- Risk scoring completed\n"
        "- Policy enforcement completed\n"
        "- Request telemetry was logged\n\n"
        "Use **Simulation Mode** or run Voreenth locally with **Local Ollama**."
    )


def _rate_limit_message() -> str:
    return (
        "## ⚠️ Cloud LLM Rate Limit Reached\n\n"
        "The hosted Cloud LLM is temporarily unavailable or has reached its current rate limit.\n\n"
        "Voreenth successfully completed:\n\n"
        "✅ Runtime Prompt Inspection\n"
        "✅ Risk Scoring\n"
        "✅ Policy Enforcement\n"
        "✅ SQLite Telemetry Logging\n\n"
        "Please try again later, switch to **Simulation Mode**, or run Voreenth locally using "
        "**Local Ollama**."
    )


def _timeout_message() -> str:
    return (
        "## ⚠️ Cloud LLM Timeout\n\n"
        "The hosted model backend did not respond within the expected time.\n\n"
        "Voreenth successfully completed prompt inspection, risk scoring, policy enforcement, "
        "and telemetry logging.\n\n"
        "Please retry shortly or switch to **Simulation Mode**."
    )


def _unavailable_message() -> str:
    return (
        "## ⚠️ Cloud LLM Unavailable\n\n"
        "The hosted model backend is currently unavailable.\n\n"
        "Voreenth successfully completed runtime inspection, risk scoring, policy enforcement, "
        "and telemetry logging.\n\n"
        "Please retry later, use **Simulation Mode**, or run Voreenth locally with **Local Ollama**."
    )


def ask_cloud_llm(prompt: str, model_name: str = DEFAULT_CLOUD_MODEL) -> str:
    api_key = _get_cloud_api_key()

    if not api_key:
        return _not_configured_message()

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
            CLOUD_LLM_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )

        if response.status_code == 429:
            return _rate_limit_message()

        response.raise_for_status()
        data = response.json()

        return clean_model_response(data["choices"][0]["message"]["content"])

    except requests.Timeout:
        return _timeout_message()

    except requests.RequestException:
        return _unavailable_message()

    except (KeyError, IndexError, TypeError, ValueError):
        return (
            "## ⚠️ Cloud LLM Response Error\n\n"
            "The hosted model returned an unexpected response format.\n\n"
            "Voreenth still completed prompt inspection, risk scoring, policy enforcement, "
            "and telemetry logging.\n\n"
            "Please retry later or switch to **Simulation Mode**."
        )


def ask_ollama(prompt: str, model_name: str = DEFAULT_LOCAL_MODEL) -> str:
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

    return clean_model_response(data.get("response", ""))


def ask_simulation(prompt: str) -> str:
    return (
        "### Simulation Mode Response\n\n"
        "Voreenth successfully inspected this prompt and allowed it through the runtime "
        "security gateway.\n\n"
        "In a production deployment, this approved request would be forwarded to the "
        "configured enterprise model backend, such as Azure OpenAI, Amazon Bedrock, "
        "Google Vertex AI, Anthropic Claude, or a self-hosted model.\n\n"
        "This simulation confirms the security workflow executed successfully:\n\n"
        "- Prompt inspection completed\n"
        "- Risk scoring completed\n"
        "- Policy decision returned `ALLOW`\n"
        "- Telemetry logged to SQLite"
    )


def ask_llm(prompt: str, backend: str, model_name: str) -> str:
    if backend == BACKEND_CLOUD:
        return ask_cloud_llm(prompt, model_name=model_name)

    if backend == BACKEND_LOCAL:
        return ask_ollama(prompt, model_name=model_name)

    return ask_simulation(prompt)


def check_ollama_health() -> bool:
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False
