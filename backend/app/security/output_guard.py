"""
Output security guardrail.
Scans every LLM response before it leaves the API.
Defends against: PII leakage, data exfiltration, reflected XSS.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass

from app.monitoring.metrics import security_pii_detections_total


@dataclass
class OutputGuardResult:
    safe: bool
    sanitised: str
    detections: list[tuple[str, str]]  # [(entity_type, matched_value), ...]


# ─────────────────────────────────────────────────────────────────────────────
# PII detection patterns
# ─────────────────────────────────────────────────────────────────────────────

_PII_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("EMAIL",        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("PHONE_UK",     re.compile(r"\b(?:(?:\+44|0044|0)\s?(?:\d\s?){9,10})\b")),
    ("PHONE_INTL",   re.compile(r"\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,9}")),
    ("NI_NUMBER",    re.compile(r"\b[A-Z]{2}\d{6}[ABCD]\b", re.IGNORECASE)),
    ("IP_ADDRESS",   re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("API_KEY",      re.compile(r"\b[A-Za-z0-9]{32,}\b")),  # long random strings
    ("PASSWORD_CTX", re.compile(r"(?i)(?:password|passwd|secret|token)\s*[=:]\s*\S+")),
    ("CREDIT_CARD",  re.compile(r"\b(?:\d{4}[\s\-]?){3}\d{4}\b")),
]

# Safe IP ranges to whitelist (private/loopback — not PII)
_SAFE_IP_PATTERN = re.compile(
    r"^(?:127\.|10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.|0\.0\.0\.0)"
)

# XSS patterns to strip from output
_XSS_PATTERNS = re.compile(
    r"<\s*(?:script|iframe|object|embed|form|input|button|link|meta|style)[^>]*>.*?</\s*\w+\s*>|"
    r"javascript\s*:",
    re.IGNORECASE | re.DOTALL,
)


class OutputGuard:
    """
    Scans LLM responses for PII and XSS before returning to the client.
    Behaviour:
      - BLOCK the response if high-risk PII found (email, NI, credit card, password)
      - REDACT moderate PII (phone numbers, generic IPs) with [REDACTED-<type>]
      - STRIP XSS payloads
      - HTML-escape the final output
    """

    _HIGH_RISK_TYPES = {"EMAIL", "NI_NUMBER", "CREDIT_CARD", "PASSWORD_CTX", "API_KEY"}

    def scan(self, text: str) -> OutputGuardResult:
        detections: list[tuple[str, str]] = []
        working = text

        # ── XSS stripping ──────────────────────────────────────────────────
        working = _XSS_PATTERNS.sub("", working)

        # ── PII detection ──────────────────────────────────────────────────
        for entity_type, pattern in _PII_PATTERNS:
            matches = pattern.findall(working)
            for match in matches:
                # Skip private IP ranges
                if entity_type == "IP_ADDRESS" and _SAFE_IP_PATTERN.match(match):
                    continue
                # Skip very short "API keys" that are just long words
                if entity_type == "API_KEY" and len(match) < 36:
                    continue

                detections.append((entity_type, match))
                security_pii_detections_total.labels(entity_type=entity_type).inc()

                if entity_type in self._HIGH_RISK_TYPES:
                    # Block entirely — caller will return escalation or generic error
                    return OutputGuardResult(
                        safe=False,
                        sanitised="",
                        detections=detections,
                    )
                else:
                    # Redact moderate PII in-place
                    working = working.replace(match, f"[REDACTED-{entity_type}]")

        # ── Final HTML escape ──────────────────────────────────────────────
        sanitised = html.escape(working)

        return OutputGuardResult(safe=True, sanitised=sanitised, detections=detections)


# Module-level singleton
_output_guard: OutputGuard | None = None


def get_output_guard() -> OutputGuard:
    global _output_guard
    if _output_guard is None:
        _output_guard = OutputGuard()
    return _output_guard
