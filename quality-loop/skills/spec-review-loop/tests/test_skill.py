"""6.2 SKILL.mdのdescription形式と 6.3 evalsの起動・非起動例。"""
from __future__ import annotations

import json

from conftest import SKILL


def frontmatter() -> str:
    return (SKILL / 'SKILL.md').read_text(encoding='utf-8').split('---', 2)[1]


def test_description_meets_explicit_invocation_contract():
    fm = frontmatter()
    assert 'name: spec-review-loop' in fm
    # quality-loop-skill-deploymentの明示起動要件（適用範囲・明示依頼例・非発火例）と同じ形式
    for phrase in ('description:', '現在のメッセージ', '明示的に依頼', '正例:', 'では使用しない', 'OpenSpec apply'):
        assert phrase in fm, phrase


def test_skill_body_covers_steps_handoff_and_routing():
    body = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    for phrase in ('commit-round', 'review', 'r<N>_report.md', 'review-standalone', 'blind-qa-cycle', 'quality-qa',
                   'quality-review', '--confirm', '--accept-residual', 'refreeze', 'prune', 'doctor'):
        assert phrase in body, phrase


def test_evals_have_three_or_more_positive_and_negative_cases():
    payload = json.loads((SKILL / 'evals' / 'evals.json').read_text(encoding='utf-8'))
    assert payload['skill_name'] == 'spec-review-loop'
    cases = payload['activation_cases']
    assert len(cases) == len({c['id'] for c in cases})
    assert all(c['prompt'] and c['reason'] and isinstance(c['expected_trigger'], bool) for c in cases)
    assert sum(c['expected_trigger'] for c in cases) >= 3
    assert sum(not c['expected_trigger'] for c in cases) >= 3


def test_runtime_uses_stdlib_only():
    import ast
    import sys
    allowed = set(sys.stdlib_module_names)
    for path in (SKILL / 'runtime' / 'spec_review_loop').glob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module]
            else:
                continue
            for name in names:
                assert name.split('.')[0] in allowed, f'{path.name}: {name}'
