"""1.1 スキーマ検証と 1.2 Reviewer契約の対応。"""
from __future__ import annotations

import copy
import re

import pytest

from conftest import SKILL
from spec_review_loop import gate, schema

SHA_A, SHA_B = 'a' * 40, 'b' * 40
CRITERIA = {'change_id': 'x', 'fingerprint': 'f' * 64,
            'criteria': [{'id': 'T-1.1', 'text': '1.1 実装する'}, {'id': 'S-cap-1.1', 'text': 'Requirement: R (ADDED)\nScenario: S'}],
            'checks': [{'id': 'CHK-VALIDATE'}]}


def valid_review() -> dict:
    return {
        'schema_version': 1, 'change_id': 'x', 'round': 1, 'base_sha': SHA_A, 'round_sha': SHA_B,
        'criteria_fingerprint': 'f' * 64, 'reviewer': {'tool': 'codex', 'version': '1', 'model': 'm'},
        'criteria': [{'id': c['id'], 'text': c['text'], 'verdict': 'PASS', 'evidence': 'a.py:1'} for c in CRITERIA['criteria']],
        'checks': [{'id': 'CHK-VALIDATE', 'status': 'PASS', 'exit_code': 0, 'reason': 'ok'}],
        'findings': [{'id': 'F-001', 'kind': 'defect', 'severity': 'low', 'criterion_ids': ['T-1.1'], 'location': 'a.py:3',
                      'description': 'd', 'recommendation': 'r', 'status': 'new'}],
        'proposals': [{'id': 'P-001', 'description': 'd', 'rationale': 'r'}], 'summary': 's',
    }


def errors_of(review: dict) -> list[str]:
    errs, _ = gate.structural_errors(review, CRITERIA, base_sha=SHA_A, round_sha=SHA_B, round_no=1, previous_open=[])
    return errs


def test_valid_review_passes_schema_and_structure():
    assert schema.validate(valid_review()) == []
    assert errors_of(valid_review()) == []


@pytest.mark.parametrize('field', ['criteria', 'checks', 'reviewer', 'base_sha', 'round_sha', 'findings', 'proposals'])
def test_missing_required_field_is_rejected(field):
    review = valid_review()
    del review[field]
    assert any(field in e for e in schema.validate(review))


@pytest.mark.parametrize('path,value', [
    (('criteria', 0, 'verdict'), 'OK'), (('checks', 0, 'status'), 'SKIPPED'), (('findings', 0, 'status'), 'open'),
    (('findings', 0, 'severity'), 'blocker'), (('base_sha',), 'abc'), (('reviewer', 'tool'), 'other'),
])
def test_invalid_enum_or_pattern_is_rejected(path, value):
    review = valid_review()
    node = review
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    assert schema.validate(review)


def test_duplicate_or_missing_criterion_id_is_structural_error():
    dup = valid_review()
    dup['criteria'][1] = copy.deepcopy(dup['criteria'][0])
    assert any('基準ID' in e for e in errors_of(dup))
    missing = valid_review()
    missing['criteria'].pop()
    assert any('欠落' in e for e in errors_of(missing))
    reordered = valid_review()
    reordered['criteria'].reverse()
    assert errors_of(reordered)


def test_altered_text_or_whitespace_is_structural_error():
    altered = valid_review()
    altered['criteria'][0]['text'] = '1.1 実装しない'
    assert any('原文' in e for e in errors_of(altered))
    spaced = valid_review()
    spaced['criteria'][1]['text'] = 'Requirement: R (ADDED)  Scenario: S'
    assert any('原文' in e for e in errors_of(spaced))
    padded = valid_review()
    padded['criteria'][0]['text'] = '  1.1 実装する\n'
    assert any('原文' in e for e in errors_of(padded))  # 前後の空白も原文の改変として扱う


def test_contract_items_map_to_schema_or_gate_rules():
    contract = (SKILL / 'references' / 'reviewer_contract.md').read_text(encoding='utf-8')
    props = schema.load_schema()['properties']
    # 契約の各項目 → スキーマ項目・Gate規則
    mapping = {
        '読取り専用': None,
        '同じID・同じ原文（`text`）・同じ順序': 'criteria',
        '`PASS`／`FAIL`／`UNVERIFIED`': 'criteria',
        '`evidence`': 'criteria',
        '`checks`はCLIが': 'checks',
        'HOLD': None, 'INCONCLUSIVE': None,
        '`proposals`': 'proposals',
        '`resolved`': 'findings', '`unresolved`': 'findings', '`unverified`': 'findings', '`withdraw-proposed`': 'findings',
        '`base_sha`、`round_sha`、`criteria_fingerprint`': 'base_sha',
        '`reviewer.model`': 'reviewer',
    }
    for phrase, prop in mapping.items():
        assert phrase in contract, phrase
        if prop:
            assert prop in props
    statuses = props['findings']['items']['properties']['status']['enum']
    assert set(re.findall(r'\| `([a-z-]+)` \|', contract)) | {'new'} == set(statuses)
    assert set(gate.GATES) <= set(re.findall(r'(HOLD|FAIL|INCONCLUSIVE|PASS)', contract))
