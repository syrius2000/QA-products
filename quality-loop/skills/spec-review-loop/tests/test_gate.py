"""5.1 構造検証とGate、5.2 停止判定。spec deltaの各Scenarioを再現する。"""
from __future__ import annotations

import pytest

import json

from conftest import CHANGE, finding, git, load, make_review, report, set_review
from spec_review_loop import gate, review_round
from spec_review_loop.errors import SpecReviewError
from spec_review_loop.session import Session


def round_with(repo, tmp_path, session, n, review_kwargs, **review_args):
    report(repo, n)
    session.commit_round()
    set_review(tmp_path, make_review(repo, **review_kwargs))
    return review_round.review(session, **review_args)['record']


@pytest.fixture
def session(repo):
    s = Session(repo, CHANGE)
    s.start(None, None, None, None)
    return s


# --- 要件: レビュー結果を構造検証してGateを判定する ---

def test_missing_criterion_id_is_not_gated(repo, tmp_path, session):
    report(repo, 1)
    session.commit_round()
    review = make_review(repo)
    review['criteria'].pop(0)
    set_review(tmp_path, review)
    record = review_round.review(session)['record']
    assert record['review'] is None and any('欠落' in e for e in record['structural_errors'])
    assert record['gate']['gate'] == 'INCONCLUSIVE' and record['retry_allowed']


def test_fail_and_not_run_coexist_gives_fail(repo, tmp_path, session, monkeypatch):
    monkeypatch.setenv('FAKE_OPENSPEC_EXIT', '0')
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo, verdicts={'T-1.1': 'FAIL'}, findings=[finding('F-001')]))
    (tmp_path / 'bin' / 'openspec').unlink()  # 必須checkがERROR（未導入）
    record = review_round.review(session)['record']
    assert record['gate']['gate'] == 'FAIL'
    assert record['review']['checks'][0]['status'] == 'ERROR'
    assert any('CHK-VALIDATE: ERROR' in r for r in record['gate']['reasons'])


def test_decide_priority_and_not_run():
    base = {'criteria': [{'id': 'T-1.1', 'verdict': 'PASS'}], 'checks': [{'id': 'CHK-VALIDATE', 'status': 'NOT_RUN', 'reason': '未実行'}]}
    assert gate.decide(base)['gate'] == 'INCONCLUSIVE'
    failing = {**base, 'criteria': [{'id': 'T-1.1', 'verdict': 'FAIL'}]}
    assert gate.decide(failing)['gate'] == 'FAIL'
    assert gate.decide(failing, provenance=['base SHAが一致しません'])['gate'] == 'HOLD'
    assert gate.decide(failing, drift=True)['gate'] == 'HOLD'
    passing = {'criteria': [{'id': 'T-1.1', 'verdict': 'PASS'}], 'checks': [{'id': 'CHK-VALIDATE', 'status': 'PASS', 'reason': ''}]}
    assert gate.decide(passing)['gate'] == 'PASS'
    assert gate.decide({**passing, 'checks': [{'id': 'CHK-VALIDATE', 'status': 'FAIL', 'reason': ''}]})['gate'] == 'FAIL'


def test_out_of_scope_request_becomes_proposal(repo, tmp_path, session):
    record = round_with(repo, tmp_path, session, 1, {'findings': [finding('F-001', criterion='')]})
    assert record['gate']['gate'] == 'PASS'
    assert record['review']['findings'] == []
    assert [p['id'] for p in record['review']['proposals']] == ['F-001']
    md = (repo / 'openspec' / 'changes' / CHANGE / 'review' / 'r1_review.md').read_text(encoding='utf-8')
    assert '## 提案' in md and 'F-001' in md.split('## 提案')[1]


def test_sha_mismatch_is_hold_with_one_retry(repo, tmp_path, session):
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo, round_sha='c' * 40))
    first = review_round.review(session)['record']
    assert first['gate']['gate'] == 'HOLD' and first['retry_allowed']
    second = review_round.review(session)['record']
    assert second['gate']['gate'] == 'HOLD' and not second['retry_allowed']
    assert load(repo, 'state.json')['status'] == 'stopped'


# --- 要件: 受入基準の固定（基準ドリフト） ---

def test_drift_at_round_start_is_hold(repo, tmp_path, session):
    tasks = repo / 'openspec' / 'changes' / CHANGE / 'tasks.md'
    tasks.write_text(tasks.read_text(encoding='utf-8').replace('greetを実装', 'greetを実施'), encoding='utf-8')
    report(repo, 1)
    with pytest.raises(SpecReviewError, match='HOLD') as exc:
        session.commit_round()
    assert exc.value.details['drift']['changed'] == ['T-1.1'] and 'refreeze' in exc.value.action


def test_drift_in_round_commit_is_hold_and_refreeze_reopens(repo, tmp_path, session):
    report(repo, 1)
    session.commit_round()
    # round commitの中で基準を書き換える（commit後に改変してamend）
    tasks = repo / 'openspec' / 'changes' / CHANGE / 'tasks.md'
    tasks.write_text(tasks.read_text(encoding='utf-8').replace('greetを実装', 'greetを実施'), encoding='utf-8')
    git(repo, 'commit', '-q', '-a', '--amend', '--no-edit')
    state = load(repo, 'state.json')
    state['rounds'][-1]['sha'] = git(repo, 'rev-parse', 'HEAD').strip()
    (repo / 'openspec' / 'changes' / CHANGE / 'review' / 'state.json').write_text(json.dumps(state), encoding='utf-8')
    set_review(tmp_path, make_review(repo))
    record = review_round.review(session)['record']
    assert record['gate']['gate'] == 'HOLD' and any('T-1.1' in r for r in record['gate']['reasons'])
    assert load(repo, 'state.json')['stop_reason'] == 'hold'
    result = session.refreeze('利用者がT-1.1の文言変更を指示')
    assert result['reopened'] and result['drift']['changed'] == ['T-1.1']
    assert session.next_round(load(repo, 'state.json')) == 2


# --- 要件: 別系統Reviewer（失敗・未導入） ---

@pytest.mark.parametrize('mode', ['fail', 'garbage', 'timeout', 'write'])
def test_reviewer_failure_is_inconclusive_with_single_retry(repo, tmp_path, session, monkeypatch, mode):
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo))
    monkeypatch.setenv('FAKE_REVIEW_MODE', mode)
    first = review_round.review(session, timeout=2)
    assert first['reviewer_failed'] and first['record']['gate']['gate'] == 'INCONCLUSIVE' and first['record']['retry_allowed']
    second = review_round.review(session, timeout=2)
    assert second['record']['gate']['gate'] == 'INCONCLUSIVE' and not second['record']['retry_allowed']
    with pytest.raises(SpecReviewError, match='レビュー済み'):
        review_round.review(session, timeout=2)


def test_missing_reviewer_cli_does_not_review(repo, tmp_path, session):
    report(repo, 1)
    session.commit_round()
    (tmp_path / 'bin' / 'codex').unlink()
    with pytest.raises(SpecReviewError, match='使えません') as exc:
        review_round.review(session)
    assert 'doctor' in exc.value.action and exc.value.details['doctor']['install']
    assert load(repo, 'state.json')['rounds'][0]['attempts'] == []


# --- 要件: 停止条件 ---

def test_pass_in_round_two_stops(repo, tmp_path, session):
    round_with(repo, tmp_path, session, 1, {'verdicts': {'T-1.1': 'FAIL'}, 'findings': [finding('F-001')]})
    record = round_with(repo, tmp_path, session, 2, {'findings': [finding('F-001', 'resolved')]})
    assert record['stop'] == {'stop': True, 'reason': 'pass', 'stalled': []}
    assert 'finish' in session.status()['next'] and 'archive' in session.status()['next']


def test_same_finding_unresolved_twice_stops_before_limit(repo, tmp_path, session):
    round_with(repo, tmp_path, session, 1, {'verdicts': {'T-1.1': 'FAIL'}, 'findings': [finding('F-002')]})
    record = round_with(repo, tmp_path, session, 2, {'verdicts': {'T-1.1': 'FAIL'}, 'findings': [finding('F-002', 'unresolved')]})
    assert record['stop']['reason'] == 'stagnation' and record['stop']['stalled'] == ['F-002']
    nxt = session.status()['next']
    assert 'review-standalone' in nxt and 'blind-qa-cycle' in nxt
    report(repo, 3)
    with pytest.raises(SpecReviewError, match='停止'):
        session.commit_round()


def test_round_limit_stops_without_fourth_round(repo, tmp_path, session):
    reviews = [
        {'verdicts': {'T-1.1': 'FAIL'}, 'findings': [finding('F-001'), finding('F-002')]},
        {'verdicts': {'T-1.1': 'FAIL'}, 'findings': [finding('F-001', 'resolved'), finding('F-002', 'resolved'), finding('F-003')]},
        {'verdicts': {'T-1.1': 'UNVERIFIED'}, 'findings': [finding('F-003', 'resolved')]},
    ]
    for n, kwargs in enumerate(reviews, 1):
        record = round_with(repo, tmp_path, session, n, kwargs)
    assert record['gate']['gate'] == 'INCONCLUSIVE' and record['stop']['reason'] == 'max-rounds'
    report(repo, 4)
    with pytest.raises(SpecReviewError):
        session.commit_round()


def test_non_decreasing_open_count_is_stagnation():
    prev = {'findings': [finding('F-001')]}
    now = {'findings': [finding('F-001', 'resolved'), finding('F-002')]}
    assert gate.stop_decision('FAIL', 2, 3, now, prev) == {'stop': True, 'reason': 'stagnation', 'stalled': ['F-002']}
    better = {'findings': [finding('F-001', 'resolved')]}
    assert gate.stop_decision('FAIL', 2, 3, better, prev)['reason'] == 'continue'


def test_previous_finding_must_be_rejudged(repo, tmp_path, session):
    round_with(repo, tmp_path, session, 1, {'verdicts': {'T-1.1': 'FAIL'}, 'findings': [finding('F-001')]})
    record = round_with(repo, tmp_path, session, 2, {})
    assert any('F-001 がfindingsで再判定されていません' in e for e in record['structural_errors'])


def test_files_created_by_checks_are_not_reviewer_writes(repo, tmp_path, session):
    review_dir = repo / 'openspec' / 'changes' / CHANGE / 'review'
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / 'checks.json').write_text(json.dumps([{'id': 'CHK-TOUCH', 'argv': ['python3', '-c', "open('made_by_check.txt','w').write('x')"]}]), encoding='utf-8')
    session.refreeze('利用者がCHK-TOUCHの追加を指示')
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo))
    record = review_round.review(session)['record']
    assert record['structural_errors'] == [] and record['gate']['gate'] == 'PASS'
    assert [c['status'] for c in record['review']['checks']] == ['PASS', 'PASS']


@pytest.mark.parametrize('bad', [{'findings': [None]}, {'findings': [{**finding('F-001'), 'criterion_ids': None}]}, {'criteria': 'x'}])
def test_malformed_reviewer_output_is_inconclusive_not_internal_error(repo, tmp_path, session, bad):
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, {**make_review(repo), **bad})
    result = review_round.review(session)
    assert result['record']['review'] is None
    assert result['record']['gate']['gate'] == 'INCONCLUSIVE' and result['record']['retry_allowed']
    assert result['record']['structural_errors']


def _remove_all_criteria(repo):
    cdir = repo / 'openspec' / 'changes' / CHANGE
    (cdir / 'tasks.md').write_text('# Tasks\n', encoding='utf-8')
    (cdir / 'specs' / 'greeting' / 'spec.md').write_text('# Spec Delta\n', encoding='utf-8')


def test_all_criteria_removed_at_commit_round_is_hold(repo, session):
    _remove_all_criteria(repo)
    report(repo, 1)
    with pytest.raises(SpecReviewError, match='HOLD') as exc:
        session.commit_round()
    assert set(exc.value.details['drift']['removed']) >= {'T-1.1', 'T-1.2', 'S-greeting-1.1'}
    assert 'refreeze' in exc.value.action


def test_all_criteria_removed_in_round_commit_is_recorded_hold(repo, tmp_path, session):
    report(repo, 1)
    session.commit_round()
    _remove_all_criteria(repo)
    git(repo, 'commit', '-q', '-a', '--amend', '--no-edit')
    state = load(repo, 'state.json')
    state['rounds'][-1]['sha'] = git(repo, 'rev-parse', 'HEAD').strip()
    (repo / 'openspec' / 'changes' / CHANGE / 'review' / 'state.json').write_text(json.dumps(state), encoding='utf-8')
    record = review_round.review(session)['record']
    assert record['gate']['gate'] == 'HOLD' and any('T-1.1' in r for r in record['gate']['reasons'])
    assert load(repo, 'state.json')['stop_reason'] == 'hold'


def test_reviewer_write_error_lists_paths(repo, tmp_path, session, monkeypatch):
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo))
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'write')
    record = review_round.review(session)['record']
    assert any('INJECTED.txt' in e for e in record['structural_errors'])


def test_reviewer_and_checks_run_without_bytecode_writes(repo, tmp_path, session):
    review_dir = repo / 'openspec' / 'changes' / CHANGE / 'review'
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / 'checks.json').write_text(json.dumps([{'id': 'CHK-ENV', 'argv': ['python3', '-c', "import os,sys; sys.exit(0 if os.environ.get('PYTHONDONTWRITEBYTECODE') == '1' else 1)"]}]), encoding='utf-8')
    session.refreeze('利用者がCHK-ENVの追加を指示')
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo))
    record = review_round.review(session)['record']
    assert [c['status'] for c in record['review']['checks']] == ['PASS', 'PASS']


def test_check_that_mutates_tracked_file_does_not_affect_reviewer(repo, tmp_path, session):
    review_dir = repo / 'openspec' / 'changes' / CHANGE / 'review'
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / 'checks.json').write_text(json.dumps([{'id': 'CHK-MUTATE', 'argv': ['python3', '-c', "open('app.py','w').write('mutated')"]}]), encoding='utf-8')
    session.refreeze('利用者がCHK-MUTATEの追加を指示')
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo))
    record = review_round.review(session)['record']
    call = json.loads((tmp_path / 'reviewer.log').read_text(encoding='utf-8').splitlines()[-1])
    assert call['app'] == git(repo, 'show', f'{record["sha"]}:app.py')
    assert record['structural_errors'] == []


def test_previous_finding_returned_only_as_proposal_is_rejected(repo, tmp_path, session):
    round_with(repo, tmp_path, session, 1, {'verdicts': {'T-1.1': 'FAIL'}, 'findings': [finding('F-001')]})
    record = round_with(repo, tmp_path, session, 2, {'proposals': [{'id': 'F-001', 'description': 'd', 'rationale': 'r'}]})
    assert record['review'] is None and any('F-001' in e and '提案' in e for e in record['structural_errors'])


def test_previous_finding_without_criteria_is_kept_for_rejudgement(repo, tmp_path, session):
    round_with(repo, tmp_path, session, 1, {'verdicts': {'T-1.1': 'FAIL'}, 'findings': [finding('F-001')]})
    record = round_with(repo, tmp_path, session, 2, {'findings': [finding('F-001', 'withdraw-proposed', criterion='')]})
    assert record['structural_errors'] == [] and record['review']['findings'][0]['status'] == 'withdraw-proposed'
