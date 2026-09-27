import re
import unicodedata
from dataclasses import dataclass
from typing import List


@dataclass
class PolicyResult:
    risk_score: int
    severity: str
    risk_level: str
    decision: str
    reasons: List[str]
    categories: List[str]


# -------------------------------------------------------------------
# Normalization
# -------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Normalize common formatting, Unicode, separator, leetspeak, and
    misspelling variants before deterministic policy evaluation.
    """
    normalized = unicodedata.normalize("NFKC", text).lower()

    replacements = {
        "@": "a",
        "$": "s",
    }

    for old, new in replacements.items():
        normalized = normalized.replace(old, new)

    spelling_corrections = {
        "envoironment": "environment",
        "enviroment": "environment",
        "environement": "environment",
        "enviornment": "environment",
        "envrionment": "environment",
        "varible": "variable",
        "varibles": "variables",
        "vairables": "variables",
        "variablez": "variables",
        "instrutions": "instructions",
        "intructions": "instructions",
        "instuctions": "instructions",
        "instructons": "instructions",
        "sytem": "system",
        "systm": "system",
        "systme": "system",
        "promt": "prompt",
        "promtp": "prompt",
        "passwrod": "password",
        "passwrd": "password",
        "tokn": "token",
        "credentails": "credentials",
        "credz": "credentials",
        "secretes": "secrets",
        "socail security": "social security",
    }

    for wrong, correct in spelling_corrections.items():
        normalized = normalized.replace(wrong, correct)

    # Collapse common separators used to split security-sensitive terms.
    normalized = re.sub(r"[_\-./\\]+", " ", normalized)

    # Collapse excessive whitespace.
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


# -------------------------------------------------------------------
# Prompt injection
# -------------------------------------------------------------------

PROMPT_INJECTION_PATTERNS = [
    r"\bignore\s+(all\s+)?(the\s+)?(previous|prior|above|earlier|system|developer)\s+instruction(s)?\b",
    r"\bdisregard\s+(all\s+)?(the\s+)?(previous|prior|above|earlier|system|developer)\s+instruction(s)?\b",
    r"\bforget\s+(all\s+)?(the\s+)?(previous|prior|above|earlier|your|system|developer)\s+instruction(s)?\b",
    r"\boverride\s+(your\s+|the\s+)?instruction(s)?\b",
    r"\boverride\s+(your\s+|the\s+)?(system|developer)\s+(prompt(s)?|instruction(s)?)\b",
    r"\bbypass\s+(the\s+)?(restriction(s)?|rule(s)?|guardrail(s)?|policy|policies|security|control(s)?)\b",
    r"\bcircumvent\s+(the\s+)?(restriction(s)?|rule(s)?|guardrail(s)?|policy|policies|security|control(s)?)\b",
    r"\bdisable\s+(the\s+)?(safety|security|guardrail(s)?|filter(s)?|policy|policies)\b",
    r"\bremove\s+(the\s+)?(safety|security|guardrail(s)?|filter(s)?|restriction(s)?)\b",
    r"\bjailbreak\b",
    r"\bdeveloper\s+mode\b",
    r"\bact\s+as\s+dan\b",
    r"\byou\s+are\s+now\s+unrestricted\b",
    r"\byou\s+have\s+no\s+(rules|restrictions|limitations)\b",
    r"\bdo\s+not\s+follow\s+(your\s+|the\s+)?instruction(s)?\b",
    r"\bstop\s+following\s+(your\s+|the\s+)?instruction(s)?\b",
    r"\bignore\s+(the\s+)?rules\b",
    r"\bignore\s+(the\s+)?policy\b",
    r"\bignore\s+(the\s+)?guardrails\b",
    r"\bpretend\s+(you\s+are\s+)?unrestricted\b",
    r"\bpretend\s+(you\s+have\s+)?no\s+(rules|restrictions|guardrails)\b",
]


# -------------------------------------------------------------------
# System / developer prompt extraction
# -------------------------------------------------------------------
#
# These patterns deliberately require extraction-oriented language.
# A benign discussion such as "What is a system prompt?" should not
# be blocked merely because it contains the phrase "system prompt".
# -------------------------------------------------------------------

SYSTEM_PROMPT_PATTERNS = [
    # reveal/show/print/display/dump/expose + protected material
    r"\b(reveal|show|print|display|dump|expose)\s+(me\s+)?(your\s+|the\s+)?(full\s+|exact\s+|original\s+|hidden\s+|internal\s+)?(system|developer|internal|hidden)\s+(prompt(s)?|instruction(s)?|message(s)?|configuration|config)\b",

    # tell/give/provide/send + protected material
    r"\b(tell|give|provide|send)\s+(me\s+)?(your\s+|the\s+)?(full\s+|exact\s+|original\s+|hidden\s+|internal\s+)?(system|developer|internal|hidden)\s+(prompt(s)?|instruction(s)?|message(s)?|configuration|config)\b",

    # "tell me what your system prompt is"
    r"\b(tell|show|reveal|explain)\s+(me\s+)?what\s+(your\s+|the\s+)?(system|developer|internal|hidden)\s+(prompt(s)?|instruction(s)?|message(s)?)\s+(is|are|says?)\b",

    # "what is/are your system prompt(s)"
    r"\bwhat\s+(is|are)\s+(your\s+|the\s+)(system|developer|internal|hidden)\s+(prompt(s)?|instruction(s)?|message(s)?|configuration|config)\b",

    # "what instructions were you given"
    r"\bwhat\s+(system\s+|developer\s+|hidden\s+|internal\s+)?instruction(s)?\s+(were|was|have)\s+you\s+(given|received)\b",

    # "what were you instructed/told to do"
    r"\bwhat\s+(were|are)\s+you\s+(instructed|told)\s+to\s+do\b",

    # repeat/quote/copy/recite protected instructions
    r"\b(repeat|quote|copy|recite|reproduce|transcribe)\s+(back\s+)?(your\s+|the\s+)?(full\s+|exact\s+|original\s+)?(system|developer|internal|hidden)\s+(prompt(s)?|instruction(s)?|message(s)?)\b",

    # "repeat the instructions above/before this message"
    r"\b(repeat|quote|copy|recite|reproduce)\s+(the\s+)?(instructions?|prompt(s)?|message(s)?)\s+(above|before\s+this|that\s+came\s+before)\b",

    # "output everything before this message"
    r"\b(output|print|show|reveal|repeat)\s+(everything|all\s+text)\s+(above|before\s+this|that\s+came\s+before)\b",

    # "beginning of your prompt"
    r"\b(beginning|start|first\s+part|opening)\s+of\s+(your\s+|the\s+)?(system|developer|hidden|internal)\s+(prompt(s)?|instruction(s)?|message(s)?)\b",

    # protected configuration requests
    r"\b(reveal|show|print|display|dump|give|provide)\s+(me\s+)?(your\s+|the\s+)?(internal|hidden|system)\s+(security\s+)?(configuration|config|settings)\b",

    # security details
    r"\b(reveal|show|print|display|dump|give|provide)\s+(me\s+)?(your\s+|the\s+)?(system|internal)\s+security\s+details\b",

    # direct hidden prompt extraction
    r"\b(reveal|show|print|display|dump|give|provide)\s+(me\s+)?(your\s+|the\s+)?hidden\s+(prompt(s)?|instruction(s)?|message(s)?)\b",
]


# -------------------------------------------------------------------
# Environment / infrastructure reconnaissance
# -------------------------------------------------------------------

RECON_PATTERNS = [
    r"\b(list|show|print|dump|display|give|provide)\s+(me\s+)?(your\s+)?(all\s+)?(env|environment)\s+variable(s)?\b",
    r"\bwhat\s+(are|is)\s+(your\s+)?(env|environment)\s+variable(s)?\b",
    r"\b(list|show|print|dump|display|give|provide)\s+(me\s+)?(your\s+)?(system|runtime|server|host)\s+(info|information|details|configuration|config)\b",
    r"\b(show|display|print|dump|read|open|cat)\s+(me\s+)?\.?env\b",
    r"\b(cat|open|read|print|show|display|dump)\s+\.?env\b",
    r"\b(printenv|whoami|hostname|ifconfig|ipconfig|netstat)\b",
    r"\buname\s+(-a|a)\b",
    r"\bps\s+(aux|-ef)\b",
    r"\b(list|show|print|display|read|open)\s+(me\s+)?(your\s+)?(local\s+)?file(s)?\b",
    r"\bwhat\s+(operating\s+system|os)\s+are\s+you\s+running\b",
    r"\b(list|show|print|display)\s+(me\s+)?(your\s+)?(installed\s+)?package(s)?\b",
    r"\b(show|list|print|display)\s+(me\s+)?(your\s+)?network\s+interface(s)?\b",
    r"\b(list|show|print|display)\s+(me\s+)?(your\s+)?(mounted\s+)?drive(s)?\b",
    r"\b(show|list|print|display|read|open)\s+(me\s+)?(your\s+)?configuration\s+file(s)?\b",
    r"\bshow\s+(me\s+)?(your\s+)?path\b",
    r"\becho\s+\$?\s*path\b",
    r"\becho\s+\$?\s*home\b",
]


# -------------------------------------------------------------------
# Secrets / credentials
# -------------------------------------------------------------------

SECRET_PATTERNS = [
    r"\bsk-[A-Za-z0-9_\-]{10,}\b",
    r"\bgsk_[A-Za-z0-9_\-]{10,}\b",
    r"\bAKIA[0-9A-Z]{16}\b",
    r"\bAIza[0-9A-Za-z_\-]{20,}\b",
    r"\b(api\s*key|secret|password|passwd|pwd|token|bearer\s+token)\b\s*[:=]\s*[A-Za-z0-9_\-.]{6,}",
    r"\bgithub\s*token\b\s*[:=]\s*[A-Za-z0-9_\-]{10,}",
    r"\bprivate\s*key\b",
]


SECRET_REQUEST_PATTERNS = [
    r"\b(give|show|reveal|print|tell|list|dump|display|provide|send)\s+(me\s+)?(your\s+|the\s+)?(all\s+)?(api\s+key(s)?|token(s)?|password(s)?|secret(s)?|credential(s)?|private\s+key(s)?)\b",
    r"\b(system|internal|admin|root)\s+(password|token|secret|credential|api\s+key)\b",
    r"\b(show|reveal|list|dump|display)\s+(me\s+)?(your\s+|the\s+)?stored\s+secret(s)?\b",
    r"\b(list|show|reveal|dump)\s+(all\s+)?(your\s+|the\s+)?credential(s)?\b",
]


# -------------------------------------------------------------------
# Sensitive personal data
# -------------------------------------------------------------------

PII_VALUE_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",
    r"\b\d{16}\b",
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
]


PII_REQUEST_PATTERNS = [
    r"\b(give|show|reveal|print|tell|list|dump|display|provide)\s+(me\s+)?(.*\s+)?(social\s+security\s+number|ssn)\b",
    r"\b(customer|employee|user|patient|client)\s+(ssn|social\s+security|date\s+of\s+birth|dob|passport|credit\s+card)\b",
    r"\b(reveal|show|give|provide|dump|display)\s+(me\s+)?(personal|private|confidential)\s+(information|data|record(s)?|detail(s)?)\b",
]


# -------------------------------------------------------------------
# Detection helpers
# -------------------------------------------------------------------

def _matches(patterns: List[str], text: str) -> bool:
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )


def _add_detection(
    score: int,
    reasons: List[str],
    categories: List[str],
    score_to_add: int,
    reason: str,
    category: str,
) -> int:
    score += score_to_add

    if reason not in reasons:
        reasons.append(reason)

    if category not in categories:
        categories.append(category)

    return score


# -------------------------------------------------------------------
# Risk classification
# -------------------------------------------------------------------

def classify_severity(score: int) -> str:
    if score >= 80:
        return "Critical"

    if score >= 50:
        return "High"

    if score >= 25:
        return "Medium"

    return "Low"


def classify_risk_level(score: int) -> str:
    return classify_severity(score)


# -------------------------------------------------------------------
# Policy evaluation
# -------------------------------------------------------------------

def evaluate_prompt(prompt: str) -> dict:
    raw_text = str(prompt or "").strip()
    text = normalize_text(raw_text)
    raw_lower = raw_text.lower()

    score = 0
    reasons: List[str] = []
    categories: List[str] = []

    if not raw_text:
        return {
            "risk_score": 0,
            "severity": "Low",
            "risk_level": "Low",
            "decision": "ALLOW",
            "reasons": ["No input provided"],
            "categories": ["Input Validation"],
        }

    # Prompt injection / instruction manipulation
    if _matches(PROMPT_INJECTION_PATTERNS, text):
        score = _add_detection(
            score,
            reasons,
            categories,
            70,
            "Instruction override or prompt injection pattern detected",
            "Prompt Injection",
        )

    # System/developer/internal prompt extraction
    if _matches(SYSTEM_PROMPT_PATTERNS, text):
        score = _add_detection(
            score,
            reasons,
            categories,
            65,
            "System, developer, or internal instruction extraction attempt detected",
            "System Prompt Extraction",
        )

    # Environment / infrastructure reconnaissance
    if _matches(RECON_PATTERNS, text):
        score = _add_detection(
            score,
            reasons,
            categories,
            60,
            "System, environment, file, or infrastructure reconnaissance pattern detected",
            "Environment Reconnaissance",
        )

    # Secret values supplied in the request
    if (
        _matches(SECRET_PATTERNS, raw_lower)
        or _matches(SECRET_PATTERNS, text)
    ):
        score = _add_detection(
            score,
            reasons,
            categories,
            70,
            "Potential credential, token, API key, password, or secret detected",
            "Secret Exposure",
        )

    # Requests attempting to retrieve secrets
    if _matches(SECRET_REQUEST_PATTERNS, text):
        score = _add_detection(
            score,
            reasons,
            categories,
            70,
            "Request for credentials, secrets, tokens, or sensitive security material detected",
            "Secret Extraction Attempt",
        )

    # Sensitive personal data values
    if _matches(PII_VALUE_PATTERNS, raw_text):
        score = _add_detection(
            score,
            reasons,
            categories,
            50,
            "Potential sensitive personal data value detected",
            "Sensitive Data Exposure",
        )

    # Requests attempting to retrieve sensitive personal data
    if _matches(PII_REQUEST_PATTERNS, text):
        score = _add_detection(
            score,
            reasons,
            categories,
            55,
            "Request for regulated or personally identifiable information detected",
            "Sensitive Data Request",
        )

    # Oversized prompt
    if len(raw_text) > 3000:
        score = _add_detection(
            score,
            reasons,
            categories,
            15,
            "Prompt length exceeds local safety threshold",
            "Input Size",
        )

    score = min(score, 100)

    severity = classify_severity(score)
    risk_level = classify_risk_level(score)

    # Fail closed at High/Critical policy threshold.
    decision = "BLOCK" if score >= 50 else "ALLOW"

    if not reasons:
        reasons.append("No policy violations detected")
        categories.append("Clean Prompt")

    return {
        "risk_score": score,
        "severity": severity,
        "risk_level": risk_level,
        "decision": decision,
        "reasons": reasons,
        "categories": categories,
    }
