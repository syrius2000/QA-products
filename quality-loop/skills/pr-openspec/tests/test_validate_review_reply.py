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


@pytest.mark.parametrize('manifest', ['manifest_unapproved_exclusion.json', 'manifest_null_approver.json', 'manifest_null_reason.json'])
def test_exclusion_without_a_real_approver_and_reason_is_inconclusive(manifest):
    """承認者や理由が null・空の除外は、out_of_scopeの回答があってもPASSにしない。"""
    rc, out = run('reply_optional_out_of_scope.json', manifest)
    assert rc == 2 and out['result'] == 'INCONCLUSIVE'
    assert any('承認者と理由' in p for p in out['problems'])


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


def _run_object(tmp_path, reply_obj):
    """回答JSONを一時ファイルに書き、checkerをCLIとして実行する。"""
    path = tmp_path / 'reply.json'
    path.write_text(json.dumps(reply_obj, ensure_ascii=False), encoding='utf-8')
    proc = subprocess.run([sys.executable, str(CHECKER), '--manifest', str(FIX / 'manifest.json'), '--reply', str(path)],
                          capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout)


def _valid_reply():
    return json.loads((FIX / 'reply_pass.json').read_text(encoding='utf-8'))


def _mutate(fn):
    obj = _valid_reply()
    fn(obj)
    return obj


SCHEMA_MUTATIONS = [
    # (名前, 変更, 問題に含まれるべき語)
    ('findings_removed', lambda o: o.pop('findings'), 'findings'),
    ('unverified_items_removed', lambda o: o.pop('unverified_items'), 'unverified_items'),
    ('evidence_null', lambda o: o['criteria'][0].update(evidence=[None]), 'evidence'),
    ('evidence_empty_string', lambda o: o['criteria'][0].update(evidence=['']), 'evidence'),
    ('finding_without_observation', lambda o: o.update(findings=[{'criterion_id': o['criteria'][0]['id'], 'impact': 'x', 'how_to_verify': 'y'}]), 'observation'),
    ('finding_empty_impact', lambda o: o.update(findings=[{'criterion_id': o['criteria'][0]['id'], 'observation': 'x', 'impact': '', 'how_to_verify': 'y'}]), 'impact'),
    ('finding_extra_field', lambda o: o.update(findings=[{'criterion_id': o['criteria'][0]['id'], 'observation': 'x', 'impact': 'x', 'how_to_verify': 'y', 'severity': 'P1'}]), 'severity'),
    ('reviewer_extra_field', lambda o: o['reviewer'].update(note='x'), 'note'),
    ('criterion_extra_field', lambda o: o['criteria'][0].update(score=1), 'score'),
    ('schema_version_true', lambda o: o.update(schema_version=True), 'schema_version'),
    ('unverified_item_null', lambda o: o.update(unverified_items=[None]), 'unverified_items'),
]


@pytest.mark.parametrize('name, mutate, word', SCHEMA_MUTATIONS, ids=[m[0] for m in SCHEMA_MUTATIONS])
def test_schema_violations_are_inconclusive(tmp_path, name, mutate, word):
    """スキーマに反する回答は、必須・型・空文字・許容外フィールドのいずれでもPASSにしない。"""
    obj = _mutate(mutate)
    rc, out = _run_object(tmp_path, obj)
    assert out['result'] == 'INCONCLUSIVE', out
    assert rc == 2
    assert any(word in p for p in out['problems']), out['problems']


def test_schema_version_1_point_0_is_the_same_value_as_1(tmp_path):
    """JSON Schemaの値比較では1と1.0は同じ。正常な回答を誤ってINCONCLUSIVEにしない。"""
    obj = _mutate(lambda o: o.update(schema_version=1.0))
    rc, out = _run_object(tmp_path, obj)
    assert out['result'] == 'PASS', out
    assert rc == 0


def test_kept_findings_carry_the_finding_body():
    """nonconformingの確実な指摘は、基準IDだけでなく回答の観測・影響・確認方法を残す（P2-002）。"""
    reply = json.loads((FIX / 'reply_fail_nonconforming.json').read_text(encoding='utf-8'))
    rc, out = run('reply_fail_nonconforming.json')
    assert out['result'] == 'FAIL'
    kept = {k['criterion_id']: k for k in out['kept_findings']}
    for finding in reply['findings']:
        bucket = kept[finding['criterion_id']]['findings']
        assert any(f['observation'] == finding['observation'] and f['how_to_verify'] == finding['how_to_verify']
                   for f in bucket), bucket

