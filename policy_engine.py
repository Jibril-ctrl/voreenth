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


def normalize_text(text: str) -> str:
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
        "sytem": "system",
        "systm": "system",
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

    normalized = re.sub(r"[_\-./\\]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


PROMPT_INJECTION_PATTERNS = [
    r"\bignore\s+(all\s+)?(previous|prior|above|earlier|system|developer)\s+instruction(s)?\b",
    r"\bdisregard\s+(all\s+)?(previous|prior|above|earlier|system|developer)\s+instruction(s)?\b",
    r"\bforget\s+(all\s+)?(previous|prior|above|earlier|your|system|developer)\s+instruction(s)?\b",
    r"\boverride\s+(your\s+)?instruction(s)?\b",
    r"\bbypass\s+(restriction(s)?|rule(s)?|guardrail(s)?|policy|policies|security|control(s)?)\b",
    r"\bdisable\s+(safety|security|guardrail(s)?|filter(s)?|policy|policies)\b",
    r"\bjailbreak\b",
    r"\bdeveloper\s+mode\b",
    r"\bact\s+as\s+dan\b",
    r"\byou\s+are\s+now\s+unrestricted\b",
    r"\bdo\s+not\s+follow\s+(your\s+)?instruction(s)?\b",
    r"\bignore\s+(the\s+)?rules\b",
    r"\bignore\s+(the\s+)?policy\b",
    r"\bpretend\s+(you\s+are\s+)?unrestricted\b",
]

SYSTEM_PROMPT_PATTERNS = [
    r"\breveal\s+(your\s+)?(system|developer|internal|hidden)\s+(prompt|instruction(s)?|message|configuration|config)\b",
    r"\bshow\s+(me\s+)?(your\s+)?(system|developer|internal|hidden)\s+(prompt|instruction(s)?|message|configuration|config)\b",
    r"\bprint\s+(your\s+)?(system|developer|internal|hidden)\s+(prompt|instruction(s)?|message|configuration|config)\b",
    r"\btell\s+me\s+(your\s+)?(system|developer|internal|hidden)\s+(prompt|instruction(s)?|message|configuration|config)\b",
    r"\bwhat\s+are\s+your\s+(system|developer|internal|hidden)\s+(prompt|instruction(s)?|message|configuration|config)\b",
    r"\b(system|developer|internal|hidden)\s+(prompt|instruction(s)?|message|configuration|config)\b",
    r"\bsystem\s+security\s+details\b",
    r"\binternal\s+security\s+details\b",
    r"\bsecurity\s+configuration\b",
    r"\bhidden\s+(prompt|instruction(s)?|message)\b",
]

RECON_PATTERNS = [
    r"\b(list|show|print|dump|display|give|provide)\s+(me\s+)?(your\s+)?(all\s+)?(env|environment)\s+variable(s)?\b",
    r"\bwhat\s+(are|is)\s+(your\s+)?(env|environment)\s+variable(s)?\b",
    r"\b(list|show|print|dump|display|give|provide)\s+(me\s+)?(your\s+)?(system|runtime|server|host)\s+(info|information|details|configuration|config)\b",
    r"\bshow\s+(me\s+)?\.?env\b",
    r"\b(cat|open|read|print|show)\s+\.?env\b",
    r"\b(env|printenv)\b",
    r"\bwhoami\b",
    r"\buname\s+a\b",
    r"\bhostname\b",
    r"\bifconfig\b",
    r"\bipconfig\b",
    r"\bnetstat\b",
    r"\bps\s+aux\b",
    r"\b(list|show|print|display|read|open)\s+(me\s+)?(your\s+)?(local\s+)?file(s)?\b",
    r"\bwhat\s+(operating\s+system|os)\s+are\s+you\s+running\b",
    r"\b(list|show|print|display)\s+(installed\s+)?package(s)?\b",
    r"\b(show|list|print|display)\s+(me\s+)?network\s+interface(s)?\b",
    r"\b(list|show|print|display)\s+(mounted\s+)?drive(s)?\b",
    r"\b(show|list|print|display|read|open)\s+(me\s+)?configuration\s+file(s)?\b",
    r"\bshow\s+(me\s+)?path\b",
    r"\becho\s+\$?path\b",
    r"\becho\s+\$?home\b",
]

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
    r"\b(give|show|reveal|print|tell|list|dump|display)\s+(me\s+)?(all\s+)?(api\s+key(s)?|token(s)?|password(s)?|secret(s)?|credential(s)?|private\s+key(s)?)\b",
    r"\b(system|internal|admin|root)\s+(password|token|secret|credential|api\s+key)\b",
    r"\bshow\s+(me\s+)?stored\s+secret(s)?\b",
    r"\blist\s+(all\s+)?credential(s)?\b",
]

PII_VALUE_PATTERNS = [
    r"\b\d{3}-\d{2}-\d{4}\b",
    r"\b\d{16}\b",
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
]

PII_REQUEST_PATTERNS = [
    r"\b(give|show|reveal|print|tell|list|dump|display)\s+(me\s+)?(.*\s+)?(social\s+security\s+number|ssn)\b",
    r"\b(social\s+security\s+number|ssn)\b",
    r"\b(customer|employee|user|patient|client)\s+(ssn|social\s+security|date\s+of\s+birth|dob|passport|credit\s+card)\b",
    r"\b(personal|private|confidential)\s+(information|data|record(s)?|detail(s)?)\b",
]


def _matches(patterns: List[str], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _add_detection(score, reasons, categories, score_to_add, reason, category):
    score += score_to_add

    if reason not in reasons:
        reasons.append(reason)

    if category not in categories:
        categories.append(category)

    return score


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


def evaluate_prompt(prompt: str) -> dict:
    raw_text = prompt.strip()
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

    if _matches(PROMPT_INJECTION_PATTERNS, text):
        score = _add_detection(
            score, reasons, categories, 70,
            "Instruction override or prompt injection pattern detected",
            "Prompt Injection",
        )

    if _matches(SYSTEM_PROMPT_PATTERNS, text):
        score = _add_detection(
            score, reasons, categories, 65,
            "System, developer, or internal instruction extraction attempt detected",
            "System Prompt Extraction",
        )

    if _matches(RECON_PATTERNS, text):
        score = _add_detection(
            score, reasons, categories, 60,
            "System, environment, file, or infrastructure reconnaissance pattern detected",
            "Environment Reconnaissance",
        )

    if _matches(SECRET_PATTERNS, raw_lower) or _matches(SECRET_PATTERNS, text):
        score = _add_detection(
            score, reasons, categories, 70,
            "Potential credential, token, API key, password, or secret detected",
            "Secret Exposure",
        )

    if _matches(SECRET_REQUEST_PATTERNS, text):
        score = _add_detection(
            score, reasons, categories, 70,
            "Request for credentials, secrets, tokens, or sensitive security material detected",
            "Secret Extraction Attempt",
        )

    if _matches(PII_VALUE_PATTERNS, raw_text):
        score = _add_detection(
            score, reasons, categories, 50,
            "Potential sensitive personal data value detected",
            "Sensitive Data Exposure",
        )

    if _matches(PII_REQUEST_PATTERNS, text):
        score = _add_detection(
            score, reasons, categories, 55,
            "Request for regulated or personally identifiable information detected",
            "Sensitive Data Request",
        )

    if len(raw_text) > 3000:
        score = _add_detection(
            score, reasons, categories, 15,
            "Prompt length exceeds local safety threshold",
            "Input Size",
        )

    score = min(score, 100)

    severity = classify_severity(score)
    risk_level = classify_risk_level(score)
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
