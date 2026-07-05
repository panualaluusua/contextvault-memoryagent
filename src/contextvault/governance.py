import re
from dataclasses import dataclass


@dataclass(frozen=True)
class WriteDecision:
    outcome: str
    text: str
    reason: str


SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:api[_ -]?key|password|secret)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\b(?:sk|qwen)-[A-Za-z0-9_-]{16,}\b"),
)
INJECTION_PATTERNS = (
    re.compile(r"ignore (?:all )?(?:previous|prior) instructions", re.IGNORECASE),
    re.compile(r"system prompt", re.IGNORECASE),
)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def evaluate_write(text: str) -> WriteDecision:
    normalized = " ".join(text.split()).strip()
    if not normalized:
        return WriteDecision("block", "", "empty memory")
    if any(pattern.search(normalized) for pattern in SECRET_PATTERNS):
        return WriteDecision("block", "", "secret-like content")
    if any(pattern.search(normalized) for pattern in INJECTION_PATTERNS):
        return WriteDecision("quarantine", normalized, "prompt-injection-like content")
    redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", normalized)
    if redacted != normalized:
        return WriteDecision("redact", redacted, "email address redacted")
    return WriteDecision("allow", normalized, "policy checks passed")
