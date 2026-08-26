import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.secret_guard import sanitize, sanitize_text


def test_common_secret_forms_are_masked():
    value = "token=abc123 password:pw123 Bearer eyJabc ghp_123456789"
    masked = sanitize_text(value)
    assert "abc123" not in masked
    assert "pw123" not in masked
    assert "eyJabc" not in masked
    assert "123456789" not in masked
    assert "[REDACTED]" in masked


def test_nested_cli_event_payload_is_sanitized():
    payload = {"errors": ["secret=my-secret"], "event": {"result": "Bearer token-value"}}
    safe = sanitize(payload)
    assert "my-secret" not in str(safe)
    assert "token-value" not in str(safe)
