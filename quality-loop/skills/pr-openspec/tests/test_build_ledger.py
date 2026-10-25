"""pr-openspec: 全要求台帳の作成（build_ledger.py）の試験。一時gitリポジトリで実行する。"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / 'scripts' / 'build_ledger.py'
SPEC = '''# Spec Delta

## ADDED Requirements

### Requirement: 要求A
本文。

#### Scenario: A1
- **WHEN** a
- **THEN** b

#### Scenario: A2
- **WHEN** c
- **THEN** d

### Requirement: 要求B
本文。

#### Scenario: B1
- **WHEN** e
- **THEN** f

## MODIFIED Requirements

### Requirement: 要求C
本文。

#### Scenario: C1
- **WHEN** g
- **THEN** h

## RENAMED Requirements

- FROM: `### Requirement: 旧名`
- TO: `### Requirement: 新名`
'''


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True).stdout


def make_repo(tmp_path, text=SPEC, path='openspec/changes/c1/specs/cap/spec.md'):
    repo = tmp_path / 'repo'
    repo.mkdir()
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.email', 't@example.com')
    git(repo, 'config', 'user.name', 'test')
    target = repo / path
    target.parent.mkdir(parents=True)
    target.write_text(text, encoding='utf-8')
    git(repo, 'add', '-A')
    git(repo, 'commit', '-q', '-m', 'init')
    return repo


def run(repo, change='c1'):
    proc = subprocess.run([sys.executable, str(SCRIPT), '--root', str(repo), '--head', 'HEAD', '--change', change],
                          capture_output=True, text=True)
    return proc.returncode, json.loads(proc.stdout)


def test_ledger_covers_added_modified_and_renamed(tmp_path):
    repo = make_repo(tmp_path)
    rc, out = run(repo)
    assert rc == 0
    src = 'openspec/changes/c1/specs/cap/spec.md'
    ids = [item['id'] for item in out['ledger']]
    assert ids == [f'R:{src}#1', f'S:{src}#1.1', f'S:{src}#1.2', f'R:{src}#2', f'S:{src}#2.1',
                   f'R:{src}#3', f'S:{src}#3.1', f'R:{src}#4']
    assert all(item['required'] is True and item['exclusion'] is None for item in out['ledger'])
    assert {item['delta'] for item in out['ledger']} == {'ADDED', 'MODIFIED', 'RENAMED'}
    renamed = out['ledger'][-1]
    assert renamed['title'] == '新名（旧名: 旧名）'


def test_blob_sha_matches_git(tmp_path):
    repo = make_repo(tmp_path)
    _, out = run(repo)
    expected = git(repo, 'rev-parse', 'HEAD:openspec/changes/c1/specs/cap/spec.md').strip()
    assert all(item['blob_sha'] == expected for item in out['ledger'])
    assert out['head_sha'] == git(repo, 'rev-parse', 'HEAD').strip()


def test_scenario_outside_a_requirement_is_refused(tmp_path):
    repo = make_repo(tmp_path, text='## ADDED Requirements\n\n#### Scenario: 孤立\n')
    rc, out = run(repo)
    assert rc == 3 and out['result'] == 'USAGE' and '孤立' in out['error']


def test_change_without_specs_gives_empty_ledger_and_exit_2(tmp_path):
    repo = make_repo(tmp_path, text='# no delta\n', path='openspec/changes/other/proposal.md')
    rc, out = run(repo, change='c1')
    assert rc == 2 and out['ledger'] == []


@pytest.mark.parametrize('text, count', [
    ('## ADDED Requirements\n\n### Requirement: x\n\n#### Scenario: s1\n\n#### Scenario: s2\n', 3),
    ('## Purpose\n\n### Requirement: 無視\n\n## ADDED Requirements\n\n### Requirement: y\n', 1),
])
def test_only_delta_sections_are_read(tmp_path, text, count):
    repo = make_repo(tmp_path, text=text)
    _, out = run(repo)
    assert len(out['ledger']) == count


def test_removed_requirements_are_in_the_ledger(tmp_path):
    text = '## REMOVED Requirements\n\n### Requirement: 削除する要求\n削除理由。\n'
    repo = make_repo(tmp_path, text=text)
    rc, out = run(repo)
    assert rc == 0
    assert [(i['id'], i['delta'], i['title']) for i in out['ledger']] == [
        ('R:openspec/changes/c1/specs/cap/spec.md#1', 'REMOVED', '削除する要求')]


@pytest.mark.parametrize('text', [
    '## RENAMED Requirements\n\n- FROM: `### Requirement: 旧名`\n',
    '## RENAMED Requirements\n\n- TO: `### Requirement: 新名`\n',
    '## RENAMED Requirements\n\n- FROM: `### Requirement: A`\n- FROM: `### Requirement: B`\n- TO: `### Requirement: C`\n',
])
def test_unpaired_rename_is_refused(tmp_path, text):
    repo = make_repo(tmp_path, text=text)
    rc, out = run(repo)
    assert rc == 3 and out['result'] == 'USAGE'
