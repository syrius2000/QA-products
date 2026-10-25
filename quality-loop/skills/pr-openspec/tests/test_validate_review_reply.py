"""pr-openspec: 回答checkerの試験。計画書の「checker試験の最低ケース」に1対1で対応するフィクスチャを使う。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE.parent / 'scripts' / 'validate_review_reply.py'
FIX = HERE / 'fixtures'


def run(reply: str, manifest: str = 'manifest.json'):
    proc = subprocess.run([sys.executable, str(CHECKER), '--manifest', str(FIX / manifest), '--reply', str(FIX / reply)],
                          capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout)


CASES = [
    # (回答, 期待する結果, 期待する終了コード, 問題に含まれるべき語（空なら問題なし）)
    ('reply_pass.json', 'PASS', 0, ''),
    ('reply_pass.md', 'PASS', 0, ''),
    ('reply_fail_nonconforming.json', 'FAIL', 1, ''),
    ('reply_inconclusive_unverified.json', 'INCONCLUSIVE', 2, ''),
    ('reply_required_out_of_scope.json', 'INCONCLUSIVE', 2, '承認済みの除外'),
    ('reply_optional_out_of_scope.json', 'PASS', 0, ''),
    ('reply_head_mismatch.json', 'INCONCLUSIVE', 2, 'head_sha'),
    ('reply_base_mismatch.json', 'INCONCLUSIVE', 2, 'base_sha'),
    ('reply_request_id_mismatch.json', 'INCONCLUSIVE', 2, 'request_id'),
    ('reply_blob_mismatch.json', 'INCONCLUSIVE', 2, 'request_blob_sha'),
    ('reply_missing_criterion.json', 'INCONCLUSIVE', 2, '回答にありません'),
    ('reply_duplicate_criterion.json', 'INCONCLUSIVE', 2, '重複'),
    ('reply_unknown_criterion.json', 'INCONCLUSIVE', 2, '台帳にない'),
    ('reply_finding_unknown_criterion.json', 'INCONCLUSIVE', 2, 'findings'),
    ('reply_invalid_verdict.json', 'INCONCLUSIVE', 2, '許容外'),
    ('reply_conforms_no_evidence.json', 'INCONCLUSIVE', 2, '根拠'),
    ('reply_unverified_no_reason.json', 'INCONCLUSIVE', 2, '理由'),
    ('reply_missing_reviewer.json', 'INCONCLUSIVE', 2, 'reviewer'),
    ('reply_bad_schema_version.json', 'INCONCLUSIVE', 2, 'schema_version'),
    ('reply_invalid_json.md', 'INCONCLUSIVE', 2, 'JSON blockの構文'),
    ('reply_no_block.md', 'INCONCLUSIVE', 2, '0個'),
    ('reply_two_blocks.md', 'INCONCLUSIVE', 2, '2個'),
]


@pytest.mark.parametrize('reply, result, code, word', CASES, ids=[c[0] for c in CASES])
def test_reply_cases(reply, result, code, word):
    rc, out = run(reply)
    assert out['result'] == result
    assert rc == code
    if word:
        assert any(word in p for p in out['problems']), out['problems']
    else:
        assert out['problems'] == []


def test_markdown_and_json_give_the_same_result():
    _, from_md = run('reply_pass.md')
    _, from_json = run('reply_pass.json')
    assert from_md == from_json


def test_manifest_empty_ledger_is_inconclusive():
    rc, out = run('reply_pass.json', 'manifest_empty_ledger.json')
    assert rc == 2 and out['result'] == 'INCONCLUSIVE' and out['structure'] == 'invalid'


def test_manifest_unapproved_exclusion_is_inconclusive():
    rc, out = run('reply_pass.json', 'manifest_unapproved_exclusion.json')
    assert rc == 2 and any('承認者と理由' in p for p in out['problems'])


def test_failure_keeps_the_nonconforming_finding_even_when_structure_is_invalid(tmp_path):
    """構造に不備があっても、確実なnonconformingは kept_findings に残す（計画書の「確実なFindingは保持」）。"""
    data = json.loads((FIX / 'reply_fail_nonconforming.json').read_text(encoding='utf-8'))
    data['criteria'].append({'id': 'S:none#9.9', 'verdict': 'conforms', 'evidence': ['x']})
    reply = tmp_path / 'reply.json'
    reply.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    proc = subprocess.run([sys.executable, str(CHECKER), '--manifest', str(FIX / 'manifest.json'), '--reply', str(reply)],
                          capture_output=True, text=True)
    out = json.loads(proc.stdout)
    assert proc.returncode == 2 and out['result'] == 'INCONCLUSIVE'
    assert [k['criterion_id'] for k in out['kept_findings']] == [f'S:openspec/changes/c1/specs/cap/spec.md#1.2']


def test_usage_error_for_missing_reply_file():
    proc = subprocess.run([sys.executable, str(CHECKER), '--manifest', str(FIX / 'manifest.json'), '--reply', str(FIX / 'nope.json')],
                          capture_output=True, text=True)
    assert proc.returncode == 3 and json.loads(proc.stdout)['result'] == 'USAGE'
