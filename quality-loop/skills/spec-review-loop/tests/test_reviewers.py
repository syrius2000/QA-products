"""4.2 Reviewerアダプタ（偽Reviewerで3経路）とdoctor。"""
from __future__ import annotations

import json
import os

import pytest

from conftest import CHANGE, load, make_review, report, set_review
from spec_review_loop import review_round, reviewers
from spec_review_loop.session import Session


def reviewed(repo, tmp_path, tool, model=None, effort=None):
    session = Session(repo, CHANGE)
    session.start(tool, None, model, None, effort)
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo, tool=tool))
    return review_round.review(session)


@pytest.mark.parametrize('tool,model', [('codex', 'unknown（CLI既定）'), ('claude', 'fake-claude-model'), ('cursor', 'auto（Cursor既定）')])
def test_each_adapter_runs_read_only_in_worktree(repo, tmp_path, tool, model):
    result = reviewed(repo, tmp_path, tool)
    record = result['record']
    assert record['gate']['gate'] == 'PASS'
    binary = reviewers.get(tool).binary
    assert record['reviewer'] == {'tool': tool, 'version': f'{binary} 9.9.9-fake', 'model': model}
    call = [json.loads(line) for line in (tmp_path / 'reviewer.log').read_text(encoding='utf-8').splitlines()][-1]
    assert call['cwd'] != str(repo) and 'spec-review-' in call['cwd']
    flags = {'codex': ['--sandbox', 'read-only'], 'claude': ['--tools', 'Read,Grep,Glob'],
             'cursor': ['--mode', 'ask', '--sandbox', 'enabled', '--workspace']}[tool]
    assert all(f in call['args'] for f in flags)
    assert record['sha'] in call['prompt'] and '受入基準' in call['prompt']


def test_codex_model_from_config(repo, tmp_path):
    home = tmp_path / 'codex-home'
    home.mkdir()
    (home / 'config.toml').write_text('model = "gpt-test"\n', encoding='utf-8')
    assert reviewed(repo, tmp_path, 'codex')['record']['reviewer']['model'] == 'gpt-test'


def test_prompt_excludes_previous_pass_judgments(repo, tmp_path):
    session = Session(repo, CHANGE)
    session.start(None, None, None, None)
    report(repo, 1)
    session.commit_round()
    from conftest import finding
    set_review(tmp_path, make_review(repo, verdicts={'T-1.1': 'FAIL'}, findings=[finding('F-001')]))
    review_round.review(session)
    report(repo, 2)
    session.commit_round()
    set_review(tmp_path, make_review(repo, findings=[finding('F-001', 'resolved')]))
    review_round.review(session)
    prompt = json.loads((tmp_path / 'reviewer.log').read_text(encoding='utf-8').splitlines()[-1])['prompt']
    assert '"id": "F-001"' in prompt
    assert '"verdict"' not in prompt.split('## 出力スキーマ')[0]


def test_probe_reports_missing_cli_with_install_hint(fake_bin):
    (fake_bin / 'agent').unlink()
    result = reviewers.probe('cursor')
    assert not result['ok'] and 'agent login' in result['install']


def test_probe_reports_missing_flags(fake_bin):
    (fake_bin / 'codex').write_text('#!/bin/sh\necho old-codex\n')
    result = reviewers.probe('codex')
    assert not result['ok'] and result['missing_flags']


def test_extract_json_tolerates_fences_and_preamble():
    assert reviewers.extract_json('結果です\n```json\n{"a": 1}\n```') == {'a': 1}
    with pytest.raises(ValueError):
        reviewers.extract_json('なし')


@pytest.mark.parametrize('tool,model,expected', [
    ('codex', 'gpt-6.1-sol', ['--model', 'gpt-6.1-sol', '-c', 'model_reasoning_effort=medium']),
    ('cursor', 'gpt-5.3-codex', ['--model', 'gpt-5.3-codex[effort=medium]']),
    ('claude', 'claude-opus-5-5', ['--model', 'claude-opus-5-5', '--effort', 'medium']),
])
def test_model_and_effort_are_passed_and_recorded(repo, tmp_path, tool, model, expected):
    record = reviewed(repo, tmp_path, tool, model=model, effort='medium')['record']
    call = [json.loads(line) for line in (tmp_path / 'reviewer.log').read_text(encoding='utf-8').splitlines()][-1]
    joined = ' '.join(call['args'])
    assert ' '.join(expected) in joined
    assert record['reviewer']['model'] == f'{model}（effort medium）'
    assert load(repo, 'state.json')['effort'] == 'medium'


def test_cursor_error_result_is_reviewer_error(repo, tmp_path, fake_bin):
    (fake_bin / 'agent').write_text("#!/bin/sh\ncase \"$1\" in --version) echo 2026.10.14;; --help) echo '--print --mode --sandbox --trust --workspace --output-format --model';; "
                                    "*) cat >/dev/null; echo '{\"type\": \"result\", \"is_error\": true, \"result\": \"quota\"}';; esac\n")
    result = reviewed(repo, tmp_path, 'cursor')
    assert result['reviewer_failed'] and 'quota' in result['record']['attempts'][0]['error']


def test_invalid_effort_is_rejected(repo):
    from spec_review_loop.errors import SpecReviewError
    with pytest.raises(SpecReviewError, match='effort'):
        Session(repo, CHANGE).start(None, None, None, None, 'Medium; rm')
