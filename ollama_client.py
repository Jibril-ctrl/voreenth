import re
import requests

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3:1.7b"


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


def check_ollama_health() -> bool:
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False