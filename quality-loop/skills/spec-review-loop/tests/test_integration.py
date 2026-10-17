"""7.1 一時リポジトリで「r1 FAIL → r2 PASS → finish」を通しで実行する。"""
from __future__ import annotations

import json

from conftest import CHANGE, cli, finding, git, load, make_review, report, set_review, write


def test_fail_then_pass_then_finish(repo, tmp_path):
    base = git(repo, 'rev-parse', 'HEAD').strip()
    assert cli(repo, 'start', CHANGE)[0] == 0
    # r1: 実装が不完全 → FAIL
    write(repo / 'app.py', 'def greet(name):\n    return name\n# wip\n')
    git(repo, 'add', 'app.py')
    report(repo, 1, '途中まで実装。')
    assert cli(repo, 'commit-round', CHANGE)[0] == 0
    set_review(tmp_path, make_review(repo, verdicts={'T-1.1': 'FAIL', 'S-greeting-1.1': 'FAIL'},
                                     findings=[finding('F-001', criterion='T-1.1')]))
    code, out = cli(repo, 'review', CHANGE)
    assert code == 0 and 'Gate: FAIL' in out and 'F-001' in out
    # r2: Finding対応 → PASS
    write(repo / 'app.py', 'def greet(name):\n    return f"hello {name or \'world\'}"\n')
    tasks = repo / 'openspec' / 'changes' / CHANGE / 'tasks.md'
    tasks.write_text(tasks.read_text(encoding='utf-8').replace('- [ ]', '- [x]'), encoding='utf-8')
    git(repo, 'add', 'app.py', str(tasks))
    report(repo, 2, 'F-001に対応。検証: pytest green。')
    assert cli(repo, 'commit-round', CHANGE)[0] == 0
    set_review(tmp_path, make_review(repo, findings=[finding('F-001', 'resolved', 'T-1.1')]))
    code, out = cli(repo, 'review', CHANGE)
    assert code == 0 and 'Gate: PASS' in out
    state = load(repo, 'state.json')
    r1, r2 = state['rounds'][0]['sha'], state['rounds'][1]['sha']
    assert len(git(repo, 'log', '--format=%H', f'{base}..HEAD').split()) == 2
    # finish
    code, out = cli(repo, '--json', 'finish', CHANGE, '--confirm')
    assert code == 0
    result = json.loads(out)
    commits = git(repo, 'log', '--format=%H', f'{base}..HEAD').split()
    assert commits == [result['squashed_sha']]
    assert git(repo, 'rev-parse', 'HEAD^{tree}').strip() == git(repo, 'rev-parse', f'{result["backup_ref"]}^{{tree}}').strip()
    body = git(repo, 'log', '-1', '--format=%B')
    assert 'Spec-Review-Gate: PASS' in body and 'Spec-Review-Rounds: 2' in body
    assert f'Spec-Review-Pre-Squash: {r2}' in body and 'Spec-Review-Reviewer: codex codex 9.9.9-fake' in body
    summary = git(repo, 'show', f'HEAD:openspec/changes/{CHANGE}/review/summary.md')
    assert r1 in summary and r2 in summary and '| r1 |' in summary and '| r2 |' in summary
    tracked = git(repo, 'ls-tree', '-r', '--name-only', 'HEAD', f'openspec/changes/{CHANGE}/review/').split()
    for name in ('criteria.json', 'state.json', 'r1_report.md', 'r1_review.json', 'r1_review.md', 'r2_review.json', 'summary.md'):
        assert f'openspec/changes/{CHANGE}/review/{name}' in tracked
    assert git(repo, 'status', '--porcelain') == ''
    assert 'archive' in cli(repo, 'status', CHANGE)[1]
