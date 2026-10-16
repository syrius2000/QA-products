"""一時gitリポジトリ・偽Reviewer・偽openspecを用意する共通fixture。"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'runtime'))
sys.dont_write_bytecode = True

FAKES = Path(__file__).resolve().parent / 'fakes'
CHANGE = 'demo-change'

TASKS = """# Tasks

## 1. 実装

- [ ] 1.1 greetを実装する。検証: test_greetが通る。
- [ ] 1.2 READMEを更新する。
  続きの行も原文に含める。
"""

SPEC = """# Spec Delta

## ADDED Requirements

### Requirement: 挨拶する
システムは挨拶を返さなければならない（MUST）。

#### Scenario: 名前を渡す
- **WHEN** 名前を渡す
- **THEN** 挨拶が返る

#### Scenario: 空の名前
- **WHEN** 空文字を渡す
- **THEN** 既定の挨拶が返る

## REMOVED Requirements

### Requirement: 旧挨拶
**Reason**: 不要になった
"""


def git(repo: Path, *args: str) -> str:
    return subprocess.run(['git', *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


@pytest.fixture
def fake_bin(tmp_path, monkeypatch):
    bindir = tmp_path / 'bin'
    bindir.mkdir()
    for name in ('codex', 'claude', 'agent'):
        shutil.copy(FAKES / 'fake_reviewer.py', bindir / name)
        (bindir / name).chmod(0o755)
    shutil.copy(FAKES / 'fake_openspec.py', bindir / 'openspec')
    (bindir / 'openspec').chmod(0o755)
    git_dir = Path(shutil.which('git')).parent
    python_dir = Path(sys.executable).parent
    monkeypatch.setenv('PATH', os.pathsep.join([str(bindir), str(python_dir), str(git_dir), '/usr/bin', '/bin']))
    monkeypatch.setenv('FAKE_REVIEW_LOG', str(tmp_path / 'reviewer.log'))
    monkeypatch.setenv('FAKE_REVIEW_FILE', str(tmp_path / 'review.json'))
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'codex-home'))
    monkeypatch.delenv('FAKE_REVIEW_MODE', raising=False)
    monkeypatch.delenv('FAKE_OPENSPEC_EXIT', raising=False)
    return bindir


@pytest.fixture
def repo(tmp_path, fake_bin):
    path = tmp_path / 'repo'
    path.mkdir()
    git(path, 'init', '-q', '-b', 'master')
    git(path, 'config', 'user.name', 'Tester')
    git(path, 'config', 'user.email', 'tester@example.com')
    git(path, 'config', 'commit.gpgsign', 'false')
    write(path / 'app.py', 'def greet(name):\n    return name\n')
    cdir = path / 'openspec' / 'changes' / CHANGE
    write(cdir / 'proposal.md', '# Proposal\n\n## Why\n\n挨拶機能を追加する。理由は以下。\n')
    write(cdir / 'tasks.md', TASKS)
    write(cdir / 'specs' / 'greeting' / 'spec.md', SPEC)
    git(path, 'add', '-A')
    git(path, 'commit', '-q', '-m', 'init')
    git(path, 'switch', '-q', '-c', 'topic')
    return path


def load(repo: Path, name: str) -> dict:
    return json.loads((repo / 'openspec' / 'changes' / CHANGE / 'review' / name).read_text(encoding='utf-8'))


def make_review(repo: Path, *, verdicts: dict | None = None, findings: list | None = None,
                proposals: list | None = None, tool: str = 'codex', **overrides) -> dict:
    state, crit = load(repo, 'state.json'), load(repo, 'criteria.json')
    verdicts = verdicts or {}
    review = {
        'schema_version': 1, 'change_id': CHANGE, 'round': state['rounds'][-1]['round'],
        'base_sha': state['base_sha'], 'round_sha': state['rounds'][-1]['sha'],
        'criteria_fingerprint': crit['fingerprint'],
        'reviewer': {'tool': tool, 'version': 'fake', 'model': 'fake-model'},
        'criteria': [{'id': c['id'], 'text': c['text'], 'verdict': verdicts.get(c['id'], 'PASS'),
                      'evidence': 'app.py:1 で確認'} for c in crit['criteria']],
        'findings': findings or [], 'proposals': proposals or [], 'summary': '所見',
    }
    review.update(overrides)
    return review


def finding(fid: str, status: str = 'new', criterion: str = 'T-1.1') -> dict:
    return {'id': fid, 'kind': 'defect', 'severity': 'high', 'criterion_ids': [criterion] if criterion else [],
            'location': 'app.py:2', 'description': f'{fid}の不具合', 'recommendation': '修正する', 'status': status}


def set_review(tmp_path: Path, review: dict) -> None:
    (tmp_path / 'review.json').write_text(json.dumps(review, ensure_ascii=False), encoding='utf-8')


def cli(repo: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(SKILL / 'bin' / 'spec-review-loop-cli'), '--root', str(repo), *args],
                          capture_output=True, text=True, env=os.environ.copy())
    return proc.returncode, proc.stdout + proc.stderr


def report(repo: Path, n: int, text: str = '実装した。検証: pytest green。') -> None:
    write(repo / 'openspec' / 'changes' / CHANGE / 'review' / f'r{n}_report.md', text)
