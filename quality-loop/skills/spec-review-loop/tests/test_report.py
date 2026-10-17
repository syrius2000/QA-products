"""5.3 r<N>_review.mdとsummary.mdの生成。"""
from __future__ import annotations

from conftest import CHANGE, finding, load, make_review, report, set_review
from spec_review_loop import finish as finish_mod
from spec_review_loop import review_round
from spec_review_loop.session import Session

REVIEW_DIR = ('openspec', 'changes', CHANGE, 'review')


def read(repo, name):
    return repo.joinpath(*REVIEW_DIR, name).read_text(encoding='utf-8')


def test_review_and_summary_markdown_contain_required_items(repo, tmp_path):
    session = Session(repo, CHANGE)
    session.start(None, None, None, None)
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo, verdicts={'T-1.2': 'FAIL'}, findings=[finding('F-001', criterion='T-1.2')],
                                     proposals=[{'id': 'P-001', 'description': '命名を改善', 'rationale': '範囲外'}]))
    review_round.review(session)
    md = read(repo, 'r1_review.md')
    state = load(repo, 'state.json')
    for cid in [c['id'] for c in load(repo, 'criteria.json')['criteria']] + ['CHK-VALIDATE', 'F-001', 'P-001']:
        assert cid in md
    assert 'Gate: **FAIL**' in md and state['rounds'][0]['sha'] in md and 'codex 9.9.9-fake' in md
    report(repo, 2)
    session.commit_round()
    set_review(tmp_path, make_review(repo, findings=[finding('F-001', 'resolved', 'T-1.2')]))
    review_round.review(session)
    result = finish_mod.finish(session, None, None, confirm=True)
    summary = read(repo, 'summary.md')
    shas = [r['sha'] for r in load(repo, 'state.json')['rounds']]
    assert all(sha in summary for sha in shas)
    assert '| r1 |' in summary and 'FAIL' in summary and '**PASS**' in summary
    assert result['backup_ref'] in summary and 'codex 9.9.9-fake' in summary
    for cid in [c['id'] for c in load(repo, 'criteria.json')['criteria']] + ['CHK-VALIDATE']:
        assert f'| {cid} |' in summary
