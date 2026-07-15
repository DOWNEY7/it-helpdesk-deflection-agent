"""
Tests for the output security guardrail (PII detection + XSS stripping).
"""
from __future__ import annotations

import pytest

from app.security.output_guard import OutputGuard


@pytest.fixture
def guard():
    return OutputGuard()


# ─────────────────────────────────────────────────────────────────────────────
# Clean outputs must pass through unchanged (bar HTML escaping)
# ─────────────────────────────────────────────────────────────────────────────

CLEAN_OUTPUTS = [
    "To reset your password, visit the self-service portal. [Source: password-reset.md]",
    "Connect to the VPN using Cisco AnyConnect, then enter your credentials. [Source: vpn-cisco-anyconnect.md]",
    "Your OneDrive files sync automatically when connected to the network.",
    "Step 1: Open Settings. Step 2: Navigate to Accounts. Step 3: Click Sign In.",
]


@pytest.mark.parametrize("text", CLEAN_OUTPUTS)
def test_clean_output_passes(guard, text):
    result = guard.scan(text)
    assert result.safe is True
    assert result.sanitised  # non-empty
    assert len(result.detections) == 0


# ─────────────────────────────────────────────────────────────────────────────
# High-risk PII — must BLOCK (return safe=False)
# ─────────────────────────────────────────────────────────────────────────────

HIGH_RISK_PII_OUTPUTS = [
    ("EMAIL",        "Please contact john.doe@company.com for assistance."),
    ("NI_NUMBER",    "Your NI number is AB123456C"),
    ("CREDIT_CARD",  "Card number: 4532 1234 5678 9012"),
    ("PASSWORD_CTX", "The admin password= secretpass123 was found in config."),
    ("API_KEY",      "Use this API key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8"),
]


@pytest.mark.parametrize("entity_type,text", HIGH_RISK_PII_OUTPUTS)
def test_high_risk_pii_blocks_response(guard, entity_type, text):
    result = guard.scan(text)
    assert result.safe is False, f"{entity_type} PII was not blocked in: {text!r}"


# ─────────────────────────────────────────────────────────────────────────────
# Moderate PII — must REDACT (return safe=True with [REDACTED-TYPE])
# ─────────────────────────────────────────────────────────────────────────────

def test_phone_number_redacted(guard):
    result = guard.scan("Call the helpdesk on 07700 900000 for support.")
    assert result.safe is True
    assert "[REDACTED-PHONE_UK]" in result.sanitised


# ─────────────────────────────────────────────────────────────────────────────
# XSS stripping
# ─────────────────────────────────────────────────────────────────────────────

def test_script_tag_stripped(guard):
    result = guard.scan(
        "Here is the answer. <script>alert('xss')</script> Follow these steps."
    )
    assert "<script>" not in result.sanitised
    assert "alert" not in result.sanitised


def test_javascript_protocol_stripped(guard):
    result = guard.scan("Click here: javascript:void(0)")
    assert "javascript:" not in result.sanitised.lower()


# ─────────────────────────────────────────────────────────────────────────────
# HTML escaping
# ─────────────────────────────────────────────────────────────────────────────

def test_html_is_escaped_in_output(guard):
    result = guard.scan("Use <strong>Settings</strong> & then click OK.")
    assert result.safe is True
    assert "<strong>" not in result.sanitised


# ─────────────────────────────────────────────────────────────────────────────
# Private IP ranges should not be redacted
# ─────────────────────────────────────────────────────────────────────────────

def test_private_ip_not_redacted(guard):
    result = guard.scan("The server is at 192.168.1.1 on the local network.")
    assert result.safe is True
    assert "192.168.1.1" in result.sanitised or "[REDACTED" not in result.sanitised
