import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_author_response.scripts.execution_policy import can_execute, eligible_fast_path


def change(severity="low", **overrides):
    value = {
        "severity": severity,
        "local": True,
        "reversible": True,
        "destructive": False,
        "external_operation": False,
        "preapproved": True,
        "documentation_only": True,
        "scoped": True,
    }
    value.update(overrides)
    return value


def test_low_local_change_can_use_fast_path():
    assert eligible_fast_path(change()) is True
    assert can_execute(
        repository_policy_allows=True,
        user_authorization_covers_scope=True,
        handoff_permission=False,
        change=change(),
    ) is True


def test_medium_change_is_denied_without_handoff_permission():
    assert eligible_fast_path(change("medium")) is False
    assert can_execute(
        repository_policy_allows=True,
        user_authorization_covers_scope=True,
        handoff_permission=False,
        change=change("medium"),
    ) is False


def test_out_of_scope_or_external_change_is_denied():
    assert can_execute(
        repository_policy_allows=True,
        user_authorization_covers_scope=False,
        handoff_permission=True,
        change=change(),
    ) is False
    assert eligible_fast_path(change(external_operation=True)) is False


def test_handoff_permission_allows_non_fast_path_only_with_authorization():
    assert can_execute(
        repository_policy_allows=True,
        user_authorization_covers_scope=True,
        handoff_permission=True,
        change=change("medium"),
    ) is True
