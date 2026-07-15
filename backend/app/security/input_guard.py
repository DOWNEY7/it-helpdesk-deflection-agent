"""
Input security guardrail.
Validates every incoming user message before it reaches the LLM pipeline.
Defends against: prompt injection, jailbreaking, oversized input, OOD intent.
"""
from __future__ import annotations

import hashlib
import html
import re
from uuid import uuid4

from app.models import GuardResult, SecurityEvent, ThreatType
from app.monitoring.metrics import (
    security_blocked_requests_total,
    security_injection_detections_total,
    security_jailbreak_attempts_total,
)
from app.security.audit_log import get_audit_logger
from app.security.rate_limiter import get_rate_limiter


# ─────────────────────────────────────────────────────────────────────────────
# Pattern library — ordered by severity (most critical first)
# ─────────────────────────────────────────────────────────────────────────────

_INJECTION_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern_id, regex, description)
    ("INJ_01", r"ignore\s+(all\s+)?previous\s+instructions?", "ignore previous instructions"),
    ("INJ_02", r"you\s+are\s+now\s+(?:a|an)\s+\w+", "you are now <role>"),
    ("INJ_03", r"act\s+as\s+(?:a|an|if\s+you\s+were)", "act as"),
    ("INJ_04", r"disregard\s+(?:your|the|all)\s+\w+", "disregard instructions"),
    ("INJ_05", r"(?:^|\s)system\s*prompt\s*:", "system prompt reveal"),
    ("INJ_06", r"<\s*/?(?:system|instructions?|context|prompt)\s*>", "XML tag injection"),
    ("INJ_07", r"developer\s+mode\s*(on|enabled|activated)?", "developer mode"),
    ("INJ_08", r"\bDAN\b", "DAN jailbreak"),
    ("INJ_09", r"do\s+anything\s+now", "do anything now"),
    ("INJ_10", r"jailbreak", "jailbreak keyword"),
    ("INJ_11", r"pretend\s+(you\s+are|to\s+be)", "pretend to be"),
    ("INJ_12", r"bypass\s+(?:your|the|all|safety|content)\s*\w*", "bypass safety"),
    ("INJ_13", r"forget\s+(?:you\s+are|that\s+you|all\s+previous)", "forget instructions"),
    ("INJ_14", r"new\s+persona\b", "new persona"),
    ("INJ_15", r"(?:base64|rot13|hex)\s+encoded?\s+instructions?", "encoded instructions"),
]

# Compiled for performance
_COMPILED_PATTERNS = [
    (pid, re.compile(pattern, re.IGNORECASE | re.MULTILINE), desc)
    for pid, pattern, desc in _INJECTION_PATTERNS
]

# Keywords strongly associated with OOD / non-IT topics
_OOD_KEYWORDS = re.compile(
    r"\b(recipe|weather|sports|politic|fiction|story|poem|"
    r"creative\s+writing|roleplay|relationship|dating|"
    r"stock\s+tip|investment|medical\s+advice|legal\s+advice)\b",
    re.IGNORECASE,
)

# Minimum IT-relevance signals
_IT_SIGNALS = re.compile(
    r"\b(password|vpn|network|printer|email|outlook|teams|onedrive|"
    r"sharepoint|laptop|computer|software|install|login|account|access|"
    r"licence|license|microsoft|azure|wifi|bluetooth|monitor|keyboard|"
    r"mouse|driver|update|reset|error|crash|slow|broken|help|support|"
    r"ticket|issue|problem|cannot|can't|not\s+working|won't|failed)\b",
    re.IGNORECASE,
)


class InputGuard:
    """
    Multi-stage input validation pipeline.
    Call validate() for every incoming message.
    """

    def validate(
        self,
        text: str,
        session_id: str,
        client_ip: str = "unknown",
    ) -> GuardResult:
        """
        Run all checks in order. Returns on first failure (fail-fast).
        On success, returns the sanitised input.
        """
        audit = get_audit_logger()

        # ── Stage 1: Rate limiting ─────────────────────────────────────────
        limiter = get_rate_limiter()
        allowed, scope = limiter.check(session_id, client_ip)
        if not allowed:
            threat: ThreatType = "rate_limit_exceeded"
            severity = "medium"
            security_blocked_requests_total.labels(threat_type=threat).inc()
            from app.monitoring.metrics import security_rate_limit_hits_total
            security_rate_limit_hits_total.labels(scope=scope).inc()
            audit.record(SecurityEvent(
                session_id=session_id,
                ip_hash=hashlib.sha256(client_ip.encode()).hexdigest()[:16],
                threat_type=threat,
                severity=severity,
                action_taken="blocked",
                rule_triggered=f"RATE_LIMIT_{scope.upper()}",
                input_snippet=text[:100],
            ))
            return GuardResult(allowed=False, threat_type=threat, severity=severity,
                               rule_triggered=f"RATE_LIMIT_{scope.upper()}")

        # ── Stage 2: Input size check ──────────────────────────────────────
        from app.config import get_settings
        if len(text) > get_settings().max_input_chars:
            threat = "oversized_input"
            security_blocked_requests_total.labels(threat_type=threat).inc()
            audit.record(SecurityEvent(
                session_id=session_id,
                ip_hash=hashlib.sha256(client_ip.encode()).hexdigest()[:16],
                threat_type=threat,
                severity="low",
                action_taken="blocked",
                rule_triggered="MAX_INPUT_CHARS",
                input_snippet=text[:100],
            ))
            return GuardResult(allowed=False, threat_type=threat, severity="low",
                               rule_triggered="MAX_INPUT_CHARS")

        # ── Stage 3: Injection pattern scan ───────────────────────────────
        for pid, compiled, _desc in _COMPILED_PATTERNS:
            if compiled.search(text):
                threat = "prompt_injection"
                severity = "high"
                security_blocked_requests_total.labels(threat_type=threat).inc()
                security_injection_detections_total.labels(pattern_id=pid).inc()
                audit.record(SecurityEvent(
                    session_id=session_id,
                    ip_hash=hashlib.sha256(client_ip.encode()).hexdigest()[:16],
                    threat_type=threat,
                    severity=severity,
                    action_taken="blocked",
                    rule_triggered=pid,
                    input_snippet=text[:100],
                ))
                return GuardResult(allowed=False, threat_type=threat, severity=severity,
                                   rule_triggered=pid)

        # ── Stage 4: OOD / Jailbreak intent classification ────────────────
        has_ood = bool(_OOD_KEYWORDS.search(text))
        has_it = bool(_IT_SIGNALS.search(text))

        if has_ood and not has_it:
            threat = "jailbreak"
            security_blocked_requests_total.labels(threat_type=threat).inc()
            security_jailbreak_attempts_total.inc()
            audit.record(SecurityEvent(
                session_id=session_id,
                ip_hash=hashlib.sha256(client_ip.encode()).hexdigest()[:16],
                threat_type=threat,
                severity="medium",
                action_taken="blocked",
                rule_triggered="OOD_CLASSIFIER",
                input_snippet=text[:100],
            ))
            return GuardResult(allowed=False, threat_type=threat, severity="medium",
                               rule_triggered="OOD_CLASSIFIER")

        # ── Stage 5: Sanitise (HTML-encode, strip null bytes) ─────────────
        sanitised = html.escape(text.replace("\x00", "").strip())

        return GuardResult(allowed=True, sanitised_input=sanitised)


# Module-level singleton
_input_guard: InputGuard | None = None


def get_input_guard() -> InputGuard:
    global _input_guard
    if _input_guard is None:
        _input_guard = InputGuard()
    return _input_guard
