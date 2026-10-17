"""Reviewer出力の構造検証、Gate判定、停止判定。すべて決定論的に行う。"""
from __future__ import annotations

from . import schema

GATES = ('HOLD', 'FAIL', 'INCONCLUSIVE', 'PASS')
OPEN_STATUSES = ('new', 'unresolved', 'unverified')
DEFAULT_MAX_ROUNDS = 3


def demote_proposals(review: dict, criteria_doc: dict, keep_ids: tuple[str, ...] = ()) -> dict:
    """基準に対応しないFindingを提案へ移した新しいレビューを返す。

    前roundの未解決Finding（keep_ids）は再判定の対象なので格下げしない。
    """
    known = {c['id'] for c in criteria_doc['criteria']} | {c['id'] for c in criteria_doc['checks']}
    findings, proposals = [], list(review.get('proposals', []))
    for finding in review.get('findings', []):
        linked = [cid for cid in finding.get('criterion_ids', []) if cid in known]
        if linked or finding['id'] in keep_ids:
            findings.append({**finding, 'criterion_ids': linked})
        else:
            proposals.append({'id': finding['id'], 'description': finding['description'],
                              'rationale': '対応する受入基準がないため提案として扱う（CLIが格下げ）'})
    return {**review, 'findings': findings, 'proposals': proposals}


def structural_errors(review: dict, criteria_doc: dict, *, base_sha: str, round_sha: str,
                      round_no: int, previous_open: list[str]) -> tuple[list[str], list[str]]:
    """(スキーマ不適合, provenance不一致)を返す。前者があればGateを判定しない。"""
    errors = schema.validate(review)
    if errors:
        return errors, []
    expected = [c['id'] for c in criteria_doc['criteria']]
    actual = [c['id'] for c in review['criteria']]
    if actual != expected:
        missing = [i for i in expected if i not in actual]
        extra = [i for i in actual if i not in expected]
        dup = sorted({i for i in actual if actual.count(i) > 1})
        errors.append(f'基準IDが基準一覧と一致しません（欠落 {missing}、追加 {extra}、重複 {dup}、または順序違い）')
    else:
        for want, got in zip(criteria_doc['criteria'], review['criteria']):
            if want['text'] != got['text']:
                errors.append(f'{want["id"]}: 基準の原文が改変されています')
    check_ids = [c['id'] for c in review['checks']]
    if check_ids != [c['id'] for c in criteria_doc['checks']]:
        errors.append('check結果のIDが必須checkの一覧と一致しません')
    finding_ids = [f['id'] for f in review['findings']] + [p['id'] for p in review['proposals']]
    if len(finding_ids) != len(set(finding_ids)):
        errors.append('Finding／提案のIDが重複しています')
    present = {f['id']: f['status'] for f in review['findings']}
    proposal_ids = {p['id'] for p in review['proposals']}
    for fid in previous_open:
        if fid not in present:
            where = '（提案としてだけ返されています）' if fid in proposal_ids else ''
            errors.append(f'前roundの未解決Finding {fid} がfindingsで再判定されていません{where}')
        elif present[fid] == 'new':
            errors.append(f'前roundのFinding {fid} を新規として扱っています')
    for f in review['findings']:
        if f['status'] != 'new' and f['id'] not in previous_open:
            errors.append(f'{f["id"]}: 前roundに存在しないFindingを再判定しています')
    provenance = []
    if review['change_id'] != criteria_doc['change_id']:
        provenance.append('change IDが一致しません')
    if review['round'] != round_no:
        provenance.append(f'round番号が一致しません（期待 r{round_no}、出力 r{review["round"]}）')
    if review['base_sha'] != base_sha:
        provenance.append('base SHAが一致しません')
    if review['round_sha'] != round_sha:
        provenance.append('round SHAが一致しません')
    if review['criteria_fingerprint'] != criteria_doc['fingerprint']:
        provenance.append('基準指紋が一致しません')
    return errors, provenance


def decide(review: dict | None, *, provenance: list[str] | None = None, drift: bool = False) -> dict:
    """Gateと理由を返す。優先順位は HOLD > FAIL > INCONCLUSIVE > PASS。"""
    if drift or provenance:
        reasons = (['基準ドリフト'] if drift else []) + list(provenance or [])
        return {'gate': 'HOLD', 'reasons': reasons}
    if review is None:
        return {'gate': 'INCONCLUSIVE', 'reasons': ['有効なレビュー結果がありません']}
    failed = [c['id'] for c in review['criteria'] if c['verdict'] == 'FAIL']
    failed += [c['id'] for c in review['checks'] if c['status'] == 'FAIL']
    if failed:
        return {'gate': 'FAIL', 'reasons': [f'FAIL: {", ".join(failed)}'] + _pending_reasons(review)}
    pending = _pending_reasons(review)
    if pending:
        return {'gate': 'INCONCLUSIVE', 'reasons': pending}
    return {'gate': 'PASS', 'reasons': ['全基準と全必須checkがPASS']}


def _pending_reasons(review: dict) -> list[str]:
    reasons = [f'{c["id"]}: UNVERIFIED' for c in review['criteria'] if c['verdict'] == 'UNVERIFIED']
    reasons += [f'{c["id"]}: {c["status"]}（{c["reason"]}）' for c in review['checks'] if c['status'] in ('NOT_RUN', 'ERROR')]
    return reasons


def latest_review(rounds: list[dict]) -> tuple[int | None, dict | None]:
    """有効なレビュー結果を持つ最新roundの(番号, review)。レビュー失敗はFinding解消の根拠にしない。"""
    for r in reversed(rounds):
        if r.get('review'):
            return r['round'], r['review']
    return None, None


def open_findings(review: dict | None) -> list[str]:
    if not review:
        return []
    return [f['id'] for f in review['findings'] if f['status'] in OPEN_STATUSES]


def stop_decision(gate: str, round_no: int, max_rounds: int, review: dict | None, previous: dict | None) -> dict:
    """停止するかと、その理由を返す。"""
    if gate == 'HOLD':
        return {'stop': True, 'reason': 'hold', 'stalled': []}
    if gate == 'PASS':
        return {'stop': True, 'reason': 'pass', 'stalled': []}
    stalled = _stalled(review, previous)
    if stalled is not None:
        return {'stop': True, 'reason': 'stagnation', 'stalled': stalled}
    if round_no >= max_rounds:
        return {'stop': True, 'reason': 'max-rounds', 'stalled': []}
    return {'stop': False, 'reason': 'continue', 'stalled': []}


def _stalled(review: dict | None, previous: dict | None) -> list[str] | None:
    """停滞ならFinding IDの一覧（数の非減少だけなら現在の未解決一覧）を返す。"""
    if not review or not previous:
        return None
    prev_open = set(open_findings(previous))
    repeated = [f['id'] for f in review['findings'] if f['status'] == 'unresolved' and f['id'] in prev_open]
    if repeated:
        return repeated
    now_open = open_findings(review)
    if prev_open and len(now_open) >= len(prev_open):
        return now_open
    return None
