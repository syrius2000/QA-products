"""add-in-agent-review-controls: 実行中の進行確認・人の指示・改ざん検知・Reviewer切替。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import pytest

from conftest import CHANGE, SKILL, cli, finding, git, load, make_review, report, set_review, write

REVIEW = lambda repo: repo / 'openspec' / 'changes' / CHANGE / 'review'  # noqa: E731


def begin(repo, *flags):
    assert cli(repo, 'start', CHANGE, *flags)[0] == 0
    report(repo, 1)
    assert cli(repo, 'commit-round', CHANGE)[0] == 0


def background_review(repo, *extra):
    cmd = [sys.executable, str(SKILL / 'bin' / 'spec-review-loop-cli'), '--root', str(repo), 'review', CHANGE, *extra]
    return subprocess.Popen(cmd, env=os.environ.copy(), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def wait_for(predicate, seconds=15):
    end = time.time() + seconds
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.1)
    return False


# --- 1. 実行中の進行確認 ---

def test_log_streams_and_status_reports_running(repo, tmp_path, monkeypatch):
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'stream')
    begin(repo)
    set_review(tmp_path, make_review(repo))
    log = REVIEW(repo) / 'r1_reviewer.log'
    proc = background_review(repo)
    assert wait_for(lambda: log.exists() and 'progress 1' in log.read_text(encoding='utf-8'))
    first = log.stat().st_size
    code, out = cli(repo, 'status', CHANGE)                      # 実行中でも読取りだけで返る
    assert code == 0 and '実行中' in out and f'PID {proc.pid}' in out and 'progress' in out
    code, out = cli(repo, 'review', CHANGE)                      # 二重実行は拒否
    assert code == 2 and '実行中' in out
    proc.communicate(timeout=30)
    assert proc.returncode == 0
    assert log.stat().st_size > first                            # 実行中にログが増えた
    text = log.read_text(encoding='utf-8')
    assert 'progress 4' in text and 'end returncode=0' in text
    assert not (REVIEW(repo) / '.review.lock').exists()          # ロックは解放される
    assert 'Gate: PASS' in cli(repo, 'status', CHANGE)[1] or load(repo, 'state.json')['rounds'][0]['gate']['gate'] == 'PASS'


def test_log_and_lock_never_enter_commits(repo, tmp_path, monkeypatch):
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'stream')
    monkeypatch.setenv('FAKE_STREAM_STEPS', '1')
    begin(repo)
    set_review(tmp_path, make_review(repo, verdicts={'T-1.1': 'FAIL'}, findings=[finding('F-001')]))
    assert cli(repo, 'review', CHANGE)[0] == 0
    assert (REVIEW(repo) / 'r1_reviewer.log').exists()
    assert git(repo, 'status', '--porcelain').count('.log') == 0
    write(repo / 'app.py', 'def greet(name):\n    return name or "x"\n')
    git(repo, 'add', 'app.py')
    report(repo, 2)
    assert cli(repo, 'commit-round', CHANGE)[0] == 0
    tracked = git(repo, 'ls-files').split()
    assert not any(name.endswith('.log') or name.endswith('.review.lock') for name in tracked)


def test_stale_lock_is_discarded(repo, tmp_path):
    begin(repo)
    set_review(tmp_path, make_review(repo))
    write(REVIEW(repo) / '.review.lock', json.dumps({'pid': 2 ** 22 + 12345, 'round': 1, 'tool': 'codex', 'started_at': 'x'}))
    code, out = cli(repo, 'review', CHANGE)
    assert code == 0 and 'Gate: PASS' in out


# --- 2. 人の指示と一時停止 ---

def test_instruct_requires_message_and_report_carries_it_verbatim(repo, tmp_path):
    begin(repo)
    set_review(tmp_path, make_review(repo, verdicts={'T-1.1': 'FAIL'}, findings=[finding('F-001')]))
    assert cli(repo, 'review', CHANGE)[0] == 0
    code, out = cli(repo, 'instruct', CHANGE, '--message', '   ')
    assert code == 2 and '人の発言' in out
    assert cli(repo, 'instruct', CHANGE, '--message', 'F-001を優先して直して')[0] == 0
    write(repo / 'app.py', 'def greet(name):\n    return name or "x"\n')
    git(repo, 'add', 'app.py')
    report(repo, 2, 'F-001を修正した。')
    code, out = cli(repo, 'commit-round', CHANGE)                 # 原文なし → 拒否
    assert code == 2 and 'F-001を優先して直して' in out
    report(repo, 2, 'F-001を修正した。\n指示: F-001を優先して直して\n')
    assert cli(repo, 'commit-round', CHANGE)[0] == 0
    inst = load(repo, 'state.json')['instructions']
    assert inst[0]['text'] == 'F-001を優先して直して' and inst[0]['consumed_round'] == 2


def test_pause_round_blocks_until_instruct(repo, tmp_path):
    begin(repo, '--pause', 'round')
    set_review(tmp_path, make_review(repo, verdicts={'T-1.1': 'FAIL'}, findings=[finding('F-001')]))
    assert cli(repo, 'review', CHANGE)[0] == 0
    assert load(repo, 'state.json')['awaiting_user'] is True
    write(repo / 'app.py', 'def greet(name):\n    return name or "x"\n')
    git(repo, 'add', 'app.py')
    report(repo, 2, 'F-001を修正した。\n指示: そのまま続けて\n')
    code, out = cli(repo, 'commit-round', CHANGE)
    assert code == 2 and '一時停止' in out
    assert '人の発言' in cli(repo, 'status', CHANGE)[1] or 'instruct' in cli(repo, 'status', CHANGE)[1]
    assert cli(repo, 'instruct', CHANGE, '--message', 'そのまま続けて')[0] == 0
    assert cli(repo, 'commit-round', CHANGE)[0] == 0


def test_pause_does_not_wait_when_loop_stops(repo, tmp_path):
    begin(repo, '--pause', 'round')
    set_review(tmp_path, make_review(repo))
    assert cli(repo, 'review', CHANGE)[0] == 0
    state = load(repo, 'state.json')
    assert state['status'] == 'stopped' and state['awaiting_user'] is False


def test_instruction_added_during_review_is_not_lost(repo, tmp_path, monkeypatch):
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'stream')
    begin(repo)
    set_review(tmp_path, make_review(repo, verdicts={'T-1.1': 'FAIL'}, findings=[finding('F-001')]))
    proc = background_review(repo)
    assert wait_for(lambda: (REVIEW(repo) / '.review.lock').exists())
    assert cli(repo, 'instruct', CHANGE, '--message', 'レビュー中に出した指示')[0] == 0
    proc.communicate(timeout=30)
    state = load(repo, 'state.json')
    assert [i['text'] for i in state['instructions']] == ['レビュー中に出した指示']
    assert state['rounds'][0]['gate']['gate'] == 'FAIL'


# --- 3. 改ざん検知 ---

def passed_loop(repo, tmp_path):
    begin(repo)
    set_review(tmp_path, make_review(repo))
    assert cli(repo, 'review', CHANGE)[0] == 0


def test_tampered_review_json_is_hold(repo, tmp_path):
    passed_loop(repo, tmp_path)
    assert 'HOLD' not in cli(repo, 'status', CHANGE)[1]
    path = REVIEW(repo) / 'r1_review.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['gate']['gate'] = 'PASS'
    data['review']['summary'] = '書き換え'
    path.write_text(json.dumps(data), encoding='utf-8')
    code, out = cli(repo, 'status', CHANGE)
    assert 'HOLD' in out and 'r1_review.json' in out
    git(repo, 'add', '-A')
    code, out = cli(repo, 'finish', CHANGE, '--confirm')
    assert code == 2 and 'HOLD' in out and git(repo, 'log', '--oneline').count('\n') == 2  # squashされていない（init と r1）
    code, out = cli(repo, 'commit-round', CHANGE)
    assert code == 2 and 'HOLD' in out


def test_tampered_prompt_is_hold(repo, tmp_path):
    passed_loop(repo, tmp_path)
    (REVIEW(repo) / 'r1_prompt.md').write_text('別のプロンプト', encoding='utf-8')
    code, out = cli(repo, 'review', CHANGE)
    assert code == 2 and 'HOLD' in out and 'r1_prompt.md' in out


def test_old_state_without_hashes_has_no_problems(repo, tmp_path):
    passed_loop(repo, tmp_path)
    state = load(repo, 'state.json')
    for r in state['rounds']:
        r.pop('review_sha256', None)
        r.pop('prompt_sha256', None)
    for key in ('pause', 'awaiting_user', 'instructions'):
        state.pop(key, None)
    (REVIEW(repo) / 'state.json').write_text(json.dumps(state), encoding='utf-8')
    code, out = cli(repo, 'status', CHANGE)
    assert code == 0 and 'HOLD' not in out
    assert cli(repo, 'finish', CHANGE)[0] == 0                    # dry-run が通る


# --- 4. Reviewer切替 ---

def test_failed_reviewer_can_be_switched_but_not_retried(repo, tmp_path, monkeypatch):
    begin(repo)
    set_review(tmp_path, make_review(repo, tool='claude'))
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'fail')
    assert cli(repo, 'review', CHANGE)[0] == 3                    # codex 1回目
    assert cli(repo, 'review', CHANGE)[0] == 3                    # codex 再試行
    code, out = cli(repo, 'review', CHANGE)                       # 同じReviewerは上限
    assert code == 2 and '再試行の上限' in out and 'codex' in out
    assert '--reviewer' in cli(repo, 'status', CHANGE)[1]
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'ok')
    code, out = cli(repo, 'review', CHANGE, '--reviewer', 'claude')
    assert code == 0 and 'Gate: PASS' in out
    record = load(repo, 'state.json')['rounds'][0]
    assert [a['tool'] for a in record['attempts']] == ['codex', 'codex', 'claude']
    assert [a.get('error') is not None for a in record['attempts']] == [True, True, False]
    assert record['reviewer']['tool'] == 'claude' and record['gate']['gate'] == 'PASS'


def test_switch_allowed_after_max_rounds_stop(repo, tmp_path, monkeypatch):
    assert cli(repo, 'start', CHANGE, '--max-rounds', '1')[0] == 0
    report(repo, 1)
    assert cli(repo, 'commit-round', CHANGE)[0] == 0
    set_review(tmp_path, make_review(repo, tool='cursor'))
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'fail')
    cli(repo, 'review', CHANGE)
    cli(repo, 'review', CHANGE)
    assert load(repo, 'state.json')['status'] == 'stopped'
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'ok')
    code, out = cli(repo, 'review', CHANGE, '--reviewer', 'cursor')
    assert code == 0 and 'Gate: PASS' in out


def test_hold_round_is_not_switchable(repo, tmp_path):
    begin(repo)
    path = REVIEW(repo)
    # 基準ドリフト（タスク文言の変更）でHOLDにする
    tasks = repo / 'openspec' / 'changes' / CHANGE / 'tasks.md'
    tasks.write_text(tasks.read_text(encoding='utf-8').replace('greetを実装', 'greetを実施'), encoding='utf-8')
    git(repo, 'commit', '-q', '-a', '--amend', '--no-edit')
    state = load(repo, 'state.json')
    state['rounds'][-1]['sha'] = git(repo, 'rev-parse', 'HEAD').strip()
    (path / 'state.json').write_text(json.dumps(state), encoding='utf-8')
    set_review(tmp_path, make_review(repo))
    assert cli(repo, 'review', CHANGE)[0] == 0
    assert load(repo, 'state.json')['stop_reason'] == 'hold'
    code, out = cli(repo, 'review', CHANGE, '--reviewer', 'claude')
    assert code == 2


# --- 6.1 通し: 実行中にstatus確認 → 指示 → round間pause → 2 roundでPASS → finish ---

def test_end_to_end_with_controls(repo, tmp_path, monkeypatch):
    base = git(repo, 'rev-parse', 'HEAD').strip()
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'stream')
    monkeypatch.setenv('FAKE_STREAM_STEPS', '3')
    begin(repo, '--pause', 'round')
    set_review(tmp_path, make_review(repo, verdicts={'T-1.1': 'FAIL'}, findings=[finding('F-001')]))
    proc = background_review(repo)
    assert wait_for(lambda: (REVIEW(repo) / '.review.lock').exists())
    assert '実行中' in cli(repo, 'status', CHANGE)[1]
    proc.communicate(timeout=30)
    assert cli(repo, 'commit-round', CHANGE)[0] == 2                      # pause
    assert cli(repo, 'instruct', CHANGE, '--message', 'F-001だけ直す')[0] == 0
    write(repo / 'app.py', 'def greet(name):\n    return name or "x"\n')
    tasks = repo / 'openspec' / 'changes' / CHANGE / 'tasks.md'
    tasks.write_text(tasks.read_text(encoding='utf-8').replace('- [ ]', '- [x]'), encoding='utf-8')
    git(repo, 'add', 'app.py', str(tasks))
    report(repo, 2, 'F-001に対応。\n指示: F-001だけ直す\n')
    assert cli(repo, 'commit-round', CHANGE)[0] == 0
    set_review(tmp_path, make_review(repo, findings=[finding('F-001', 'resolved')]))
    assert cli(repo, 'review', CHANGE)[0] == 0
    assert load(repo, 'state.json')['stop_reason'] == 'pass'
    code, out = cli(repo, '--json', 'finish', CHANGE, '--confirm')
    assert code == 0
    result = json.loads(out)
    assert git(repo, 'log', '--format=%H', f'{base}..HEAD').split() == [result['squashed_sha']]
    assert git(repo, 'rev-parse', 'HEAD^{tree}').strip() == git(repo, 'rev-parse', f'{result["backup_ref"]}^{{tree}}').strip()
    tracked = git(repo, 'ls-tree', '-r', '--name-only', 'HEAD').split()
    assert not any(name.endswith(('.log', '.review.lock')) for name in tracked)
    assert any(name.endswith('r1_prompt.md') for name in tracked)
    assert git(repo, 'status', '--porcelain') == ''


def test_timeout_kills_descendant_processes(repo, tmp_path, monkeypatch):
    """timeoutではReviewerの子孫プロセスも止まり、孤児が残らない（tasks 1.1）。"""
    pid_file = tmp_path / 'child.pid'
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'orphan')
    monkeypatch.setenv('FAKE_CHILD_PID', str(pid_file))
    begin(repo)
    set_review(tmp_path, make_review(repo))
    code, out = cli(repo, 'review', CHANGE, '--timeout', '2')
    assert code == 3 and pid_file.exists()
    child = int(pid_file.read_text())

    def gone():
        try:
            os.kill(child, 0)
        except ProcessLookupError:
            return True
        # ゾンビはkill(0)が成功するので、状態も見る
        try:
            return open(f'/proc/{child}/stat').read().split(')')[1].split()[0] == 'Z'
        except OSError:
            return True
    assert wait_for(gone, 5)
    assert git(repo, 'worktree', 'list').count('\n') == 1                  # 一時worktreeも残らない
