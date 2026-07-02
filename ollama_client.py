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


def ask_groq(prompt: str, model_name: str = DEFAULT_GROQ_MODEL) -> str:
    api_key = _get_groq_api_key()

    if not api_key:
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

    response = requests.post(
        GROQ_ENDPOINT,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )

    response.raise_for_status()
    data = response.json()

    raw_response = data["choices"][0]["message"]["content"]
    return clean_model_response(raw_response)


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
