"""2.1 受入基準の抽出と 2.2 要件指紋・ドリフト。"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from conftest import CHANGE, SKILL, write
from spec_review_loop import criteria as crit
from spec_review_loop.errors import SpecReviewError

ARCHIVE = SKILL.parents[2] / 'openspec' / 'changes' / 'archive'
# 手作業で数えた件数（tasks.mdのチェックボックス行・spec.mdの「#### Scenario:」行）
EXPECTED = {
    '2026-10-11-improve-quality-qa-loop': (37, 25),
    '2026-10-11-require-explicit-qa-request': (5, 5),
    '2026-10-11-simplify-qa-status-display': (15, 18),
    '2026-10-11-unify-blind-qa-cycle': (11, 23),
}


@pytest.mark.parametrize('name,counts', EXPECTED.items())
def test_archived_changes_extract_expected_counts(name, counts):
    cdir = ARCHIVE / name
    if not cdir.exists():
        pytest.skip('archive済みchangeがありません')
    tasks, ignored = crit.extract_tasks(cdir / 'tasks.md')
    scenarios = crit.extract_scenarios(cdir / 'specs')
    assert (len(tasks), len(scenarios), ignored) == (*counts, 0)
    lines = (cdir / 'tasks.md').read_text(encoding='utf-8').splitlines()
    for task in tasks:
        first = task['text'].split('\n')[0]
        assert any(line.rstrip().endswith(first.split(' ', 1)[1]) for line in lines), task['id']
    ids = [s['id'] for s in scenarios]
    assert len(ids) == len(set(ids))


def test_archived_scenario_text_matches_source():
    cdir = ARCHIVE / '2026-10-11-require-explicit-qa-request'
    if not cdir.exists():
        pytest.skip('archive済みchangeがありません')
    scenarios = crit.extract_scenarios(cdir / 'specs')
    first = scenarios[0]
    assert first['id'] == 'S-quality-loop-skill-deployment-1.1'
    assert first['text'].startswith('ADDED: ### Requirement: 明示的なユーザー依頼をQA Skill起動条件とする\n#### Scenario: QA操作を明示的に依頼する\n- **WHEN**')
    source = (cdir / 'specs' / 'quality-loop-skill-deployment' / 'spec.md').read_text(encoding='utf-8')
    assert first['text'].split('\n', 1)[1] in source  # Scenario以降は原文の連続した行そのもの


def test_ids_order_and_text_in_demo_change(repo):
    doc = crit.build(repo, CHANGE)
    ids = [c['id'] for c in doc['criteria']]
    assert ids == ['T-1.1', 'T-1.2', 'S-greeting-1.1', 'S-greeting-1.2', 'S-greeting-2.0']
    assert doc['criteria'][0]['verification'] == 'test_greetが通る。'
    assert doc['criteria'][1]['text'] == '1.2 READMEを更新する。\n  続きの行も原文に含める。'
    assert doc['criteria'][4]['kind'] == 'removed'
    assert doc['criteria'][4]['text'] == 'REMOVED: ### Requirement: 旧挨拶\n**Reason**: 不要になった'
    assert [c['id'] for c in doc['checks']] == ['CHK-VALIDATE']
    assert doc['checks'][0]['argv'] == ['openspec', 'validate', '--strict', CHANGE]


def test_checkbox_toggle_keeps_fingerprint(repo):
    frozen = crit.build(repo, CHANGE)
    tasks = repo / 'openspec' / 'changes' / CHANGE / 'tasks.md'
    tasks.write_text(tasks.read_text(encoding='utf-8').replace('- [ ] 1.1', '- [x] 1.1'), encoding='utf-8')
    diff = crit.drift(frozen, crit.build(repo, CHANGE))
    assert not crit.has_drift(diff)


def test_one_character_change_is_drift(repo):
    frozen = crit.build(repo, CHANGE)
    tasks = repo / 'openspec' / 'changes' / CHANGE / 'tasks.md'
    tasks.write_text(tasks.read_text(encoding='utf-8').replace('greetを実装', 'greetを実施'), encoding='utf-8')
    diff = crit.drift(frozen, crit.build(repo, CHANGE))
    assert diff == {'added': [], 'removed': [], 'changed': ['T-1.1']}


def test_added_check_is_drift_and_checks_are_validated(repo):
    frozen = crit.build(repo, CHANGE)
    review = repo / 'openspec' / 'changes' / CHANGE / 'review'
    write(review / 'checks.json', json.dumps([{'id': 'CHK-PYTEST', 'argv': ['pytest', '-q'], 'timeout': 60}]))
    current = crit.build(repo, CHANGE)
    assert crit.drift(frozen, current)['added'] == ['CHK-PYTEST']
    for bad in ([{'id': 'chk', 'argv': ['x']}], [{'id': 'CHK-A', 'argv': 'pytest -q'}],
                [{'id': 'CHK-A', 'argv': ['x'], 'cwd': '../out'}], [{'id': 'CHK-VALIDATE', 'argv': ['x']}]):
        write(review / 'checks.json', json.dumps(bad))
        with pytest.raises(SpecReviewError):
            crit.build(repo, CHANGE)


def test_no_criteria_is_rejected(repo):
    cdir = repo / 'openspec' / 'changes' / CHANGE
    (cdir / 'tasks.md').unlink()
    (cdir / 'specs' / 'greeting' / 'spec.md').unlink()
    with pytest.raises(SpecReviewError, match='受入基準を抽出できません'):
        crit.build(repo, CHANGE)


def test_unknown_change_and_bad_id_are_rejected(repo):
    with pytest.raises(SpecReviewError, match='見つかりません'):
        crit.build(repo, 'missing')
    with pytest.raises(SpecReviewError, match='形式'):
        crit.build(repo, '../etc')


def test_duplicate_task_number_is_rejected(repo):
    tasks = repo / 'openspec' / 'changes' / CHANGE / 'tasks.md'
    tasks.write_text(tasks.read_text(encoding='utf-8') + '- [ ] 1.1 重複\n', encoding='utf-8')
    with pytest.raises(SpecReviewError, match='重複'):
        crit.build(repo, CHANGE)


def test_unnumbered_tasks_are_counted(tmp_path):
    path = write(tmp_path / 'tasks.md', '- [ ] 番号なし\n- [ ] 2.1 番号あり\n')
    tasks, ignored = crit.extract_tasks(path)
    assert [t['id'] for t in tasks] == ['T-2.1'] and ignored == 1


@pytest.mark.parametrize('old,new', [
    ('greetを実装する。検証', 'greetを実装する。 検証'),          # タスク本文中の空白
    ('- [ ] 1.1 greetを', '- [ ] 1.1  greetを'),                  # 番号後の空白
    ('test_greetが通る。\n', 'test_greetが通る。 \n'),          # 行末の空白
    ('  続きの行も', '    続きの行も'),                              # 継続行のインデント
])
def test_whitespace_change_in_task_is_drift(repo, old, new):
    frozen = crit.build(repo, CHANGE)
    tasks = repo / 'openspec' / 'changes' / CHANGE / 'tasks.md'
    text = tasks.read_text(encoding='utf-8')
    assert old in text
    tasks.write_text(text.replace(old, new, 1), encoding='utf-8')
    assert crit.has_drift(crit.drift(frozen, crit.build(repo, CHANGE)))


@pytest.mark.parametrize('old,new', [('- **THEN** 挨拶が返る', '- **THEN** 挨拶が返る '), ('#### Scenario: 名前を渡す', '#### Scenario:  名前を渡す')])
def test_whitespace_change_in_scenario_is_drift(repo, old, new):
    frozen = crit.build(repo, CHANGE)
    spec = repo / 'openspec' / 'changes' / CHANGE / 'specs' / 'greeting' / 'spec.md'
    spec.write_text(spec.read_text(encoding='utf-8').replace(old, new, 1), encoding='utf-8')
    assert crit.drift(frozen, crit.build(repo, CHANGE))['changed'] == ['S-greeting-1.1']
