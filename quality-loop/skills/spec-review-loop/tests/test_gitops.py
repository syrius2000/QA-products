"""3.1〜3.4 start／commit-round、一時worktree、finish、prune。"""
from __future__ import annotations

import pytest

from conftest import CHANGE, finding, git, load, make_review, report, set_review, write
from spec_review_loop import finish as finish_mod
from spec_review_loop import gitops, review_round
from spec_review_loop.errors import SpecReviewError
from spec_review_loop.session import Session


def started(repo):
    session = Session(repo, CHANGE)
    session.start(None, None, None, None)
    return session


def test_start_rejects_default_branch(repo):
    git(repo, 'switch', '-q', 'master')
    with pytest.raises(SpecReviewError, match='master では開始できません') as exc:
        Session(repo, CHANGE).start(None, None, None, None)
    assert 'topic branch' in exc.value.action
    assert not (repo / 'openspec' / 'changes' / CHANGE / 'review').exists()


def test_start_rejects_dirty_outside_change_and_records_base(repo):
    write(repo / 'other.txt', 'x')
    with pytest.raises(SpecReviewError, match='対象change以外'):
        Session(repo, CHANGE).start(None, None, None, None)
    (repo / 'other.txt').unlink()
    result = Session(repo, CHANGE).start(None, None, None, None)
    assert result['state']['base_sha'] == gitops.head(repo)
    assert result['state']['branch'] == 'topic'
    with pytest.raises(SpecReviewError, match='開始済み'):
        Session(repo, CHANGE).start(None, None, None, None)


def test_commit_round_requires_report(repo):
    session = started(repo)
    with pytest.raises(SpecReviewError, match='実装報告がありません'):
        session.commit_round()
    assert len(gitops.commits_since(repo, load(repo, 'state.json')['base_sha'])) == 0


def test_commit_round_rejects_untracked_and_unstaged(repo):
    session = started(repo)
    report(repo, 1)
    write(repo / 'new.py', 'x')
    with pytest.raises(SpecReviewError) as exc:
        session.commit_round()
    assert exc.value.details['paths'] == ['?? new.py']
    (repo / 'new.py').unlink()
    write(repo / 'app.py', 'changed\n')
    with pytest.raises(SpecReviewError) as exc:
        session.commit_round()
    assert exc.value.details['paths'] == [' M app.py']


def test_commit_round_commits_staged_and_review_with_trailer(repo):
    session = started(repo)
    report(repo, 1)
    write(repo / 'app.py', 'def greet(name):\n    return f"hi {name}"\n')
    git(repo, 'add', 'app.py')
    result = session.commit_round()
    message = git(repo, 'log', '-1', '--format=%B')
    assert message.startswith(f'spec-review: r1 {CHANGE}\n')
    assert f'Spec-Review-Round: {CHANGE} r1' in message
    files = git(repo, 'show', '--name-only', '--format=', 'HEAD').split()
    assert 'app.py' in files and f'openspec/changes/{CHANGE}/review/r1_report.md' in files
    assert f'openspec/changes/{CHANGE}/review/criteria.json' in files
    assert load(repo, 'state.json')['rounds'][0]['sha'] == result['sha']


@pytest.mark.parametrize('mode', ['ok', 'fail', 'timeout'])
def test_worktree_is_removed_after_review(repo, tmp_path, monkeypatch, mode):
    session = started(repo)
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo))
    monkeypatch.setenv('FAKE_REVIEW_MODE', mode)
    review_round.review(session, timeout=2)
    assert gitops.worktree_paths(repo) == [str(repo.resolve())]


def test_worktree_is_removed_on_exception(repo):
    with pytest.raises(RuntimeError):
        with gitops.review_worktree(repo, gitops.head(repo)) as wt:
            assert wt.exists()
            raise RuntimeError('boom')
    assert gitops.worktree_paths(repo) == [str(repo.resolve())]


def pass_round(repo, tmp_path, session, n=1):
    report(repo, n)
    session.commit_round()
    set_review(tmp_path, make_review(repo))
    review_round.review(session)


def test_finish_dry_run_then_squash(repo, tmp_path):
    session = started(repo)
    base = load(repo, 'state.json')['base_sha']
    pass_round(repo, tmp_path, session)
    plan = finish_mod.finish(session, None, None, confirm=False)
    assert plan['dry_run'] and gitops.head(repo) != base and len(gitops.commits_since(repo, base)) == 1
    result = finish_mod.finish(session, None, None, confirm=True)
    commits = gitops.commits_since(repo, base)
    assert len(commits) == 1 and commits[0]['sha'] == result['squashed_sha']
    assert gitops.tree_of(repo, 'HEAD') == gitops.tree_of(repo, result['backup_ref'])
    assert result['backup_ref'].startswith(f'refs/spec-review/{CHANGE}/')
    body = git(repo, 'log', '-1', '--format=%B')
    assert body.startswith(f'feat({CHANGE}): 挨拶機能を追加する\n')
    for key in ('Spec-Review: ', 'Spec-Review-Gate: PASS', 'Spec-Review-Rounds: 1', 'Spec-Review-Reviewer: codex', 'Spec-Review-Pre-Squash: '):
        assert key in body
    assert git(repo, 'status', '--porcelain') == ''


def test_finish_rejects_pushed_rounds(repo, tmp_path):
    session = started(repo)
    pass_round(repo, tmp_path, session)
    git(repo, 'update-ref', 'refs/remotes/origin/topic', 'HEAD')
    before = gitops.head(repo)
    with pytest.raises(SpecReviewError, match='force-push') as exc:
        finish_mod.finish(session, None, None, confirm=True)
    assert '明示承認' in exc.value.action and gitops.head(repo) == before


def test_finish_rejects_foreign_commit(repo, tmp_path):
    session = started(repo)
    pass_round(repo, tmp_path, session)
    write(repo / 'x.txt', 'x')
    git(repo, 'add', 'x.txt')
    git(repo, 'commit', '-q', '-m', 'unrelated')
    with pytest.raises(SpecReviewError, match='round commit以外'):
        finish_mod.finish(session, None, None, confirm=True)


def test_finish_rejects_dirty_tree(repo, tmp_path):
    session = started(repo)
    pass_round(repo, tmp_path, session)
    write(repo / 'app.py', 'dirty\n')
    with pytest.raises(SpecReviewError, match='clean'):
        finish_mod.finish(session, None, None, confirm=False)


def test_finish_restores_on_tree_mismatch(repo, tmp_path, monkeypatch):
    session = started(repo)
    pass_round(repo, tmp_path, session)
    real = gitops.commit_squash

    def tampered(root, base, message):
        write(root / 'app.py', 'tampered\n')
        git(root, 'add', 'app.py')
        return real(root, base, message)

    monkeypatch.setattr(gitops, 'commit_squash', tampered)
    before_state = load(repo, 'state.json')
    with pytest.raises(SpecReviewError, match='squash後のtreeがsquash前と一致しません') as exc:
        finish_mod.finish(session, None, None, confirm=True)
    _assert_rolled_back(repo, exc.value.details['restored_to'], before_state)
    assert (repo / 'app.py').read_text(encoding='utf-8') != 'tampered\n'  # 改変された作業ツリーも戻る
    monkeypatch.setattr(gitops, 'commit_squash', real)
    assert finish_mod.finish(session, None, None, confirm=True)['squashed_sha']  # 再実行できる


def test_finish_requires_accept_residual_when_not_pass(repo, tmp_path):
    session = started(repo)
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo, verdicts={'T-1.1': 'FAIL'}, findings=[finding('F-001')]))
    review_round.review(session)
    with pytest.raises(SpecReviewError, match='PASSではありません') as exc:
        finish_mod.finish(session, None, None, confirm=True)
    assert '--accept-residual' in exc.value.action


def test_prune_requires_confirmation(repo, tmp_path):
    session = started(repo)
    pass_round(repo, tmp_path, session)
    result = finish_mod.finish(session, None, None, confirm=True)
    round_sha = load(repo, 'state.json')['rounds'][0]['sha']
    preview = finish_mod.prune(session, confirm=False)
    assert preview['dry_run'] and round_sha in preview['unreachable_after_prune']
    assert gitops.list_refs(repo, CHANGE)
    done = finish_mod.prune(session, confirm=True)
    assert done['deleted'] == [result['backup_ref']]
    assert gitops.list_refs(repo, CHANGE) == []


def test_finish_restores_when_squash_commit_fails(repo, tmp_path, monkeypatch):
    session = started(repo)
    pass_round(repo, tmp_path, session)

    def failing(root, base, message):
        git(root, 'reset', '--soft', base)
        raise RuntimeError('commit failed')

    monkeypatch.setattr(gitops, 'commit_squash', failing)
    before_state = load(repo, 'state.json')
    with pytest.raises(SpecReviewError, match='finish前の状態へ戻しました: commit failed') as exc:
        finish_mod.finish(session, None, None, confirm=True)
    _assert_rolled_back(repo, exc.value.details['restored_to'], before_state)


def test_non_pass_finish_records_residual_findings_in_trailer(repo, tmp_path):
    session = started(repo)
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo, verdicts={'T-1.1': 'FAIL'}, findings=[finding('F-001'), finding('F-002', criterion='T-1.2')]))
    review_round.review(session)
    finish_mod.finish(session, None, '利用者がF-001・F-002を次changeで扱うと判断', confirm=True)
    body = git(repo, 'log', '-1', '--format=%B')
    assert 'Spec-Review-Gate: FAIL' in body and 'Spec-Review-Residual-Findings: F-001, F-002' in body
    assert 'Spec-Review-Residual: 利用者がF-001・F-002を次changeで扱うと判断' in body


def test_residual_findings_carry_over_when_last_review_failed(repo, tmp_path, monkeypatch):
    session = started(repo)
    report(repo, 1)
    session.commit_round()
    set_review(tmp_path, make_review(repo, verdicts={'T-1.1': 'FAIL'}, findings=[finding('F-001'), finding('F-002', criterion='T-1.2')]))
    review_round.review(session)
    report(repo, 2)
    session.commit_round()
    monkeypatch.setenv('FAKE_REVIEW_MODE', 'fail')
    review_round.review(session)
    review_round.review(session)  # 再試行も失敗 → r2は有効なレビューなし
    finish_mod.finish(session, None, '利用者が残余を受容', confirm=True)
    body = git(repo, 'log', '-1', '--format=%B')
    assert 'Spec-Review-Gate: INCONCLUSIVE' in body and 'Spec-Review-Residual-Findings: F-001, F-002' in body
    summary = git(repo, 'show', f'HEAD:openspec/changes/{CHANGE}/review/summary.md')
    assert 'r1の判定と未解決Findingを引き継ぐ' in summary and '- F-001' in summary and '- F-002' in summary


def test_finish_rejects_amended_round_commit(repo, tmp_path):
    session = started(repo)
    pass_round(repo, tmp_path, session)
    write(repo / 'app.py', 'unreviewed\n')
    git(repo, 'add', 'app.py')
    git(repo, 'commit', '-q', '--amend', '--no-edit')  # trailerは保持される
    assert 'Spec-Review-Round' in git(repo, 'log', '-1', '--format=%B')
    before = gitops.head(repo)
    with pytest.raises(SpecReviewError, match='レビュー済みのround commitと一致しません'):
        finish_mod.finish(session, None, None, confirm=False)
    assert gitops.head(repo) == before


def _assert_rolled_back(repo, round_sha, before_state):
    assert gitops.head(repo) == round_sha == before_state['rounds'][-1]['sha']
    assert load(repo, 'state.json') == before_state and before_state['status'] != 'finished'
    assert not (repo / 'openspec' / 'changes' / CHANGE / 'review' / 'summary.md').exists()
    assert gitops.list_refs(repo, CHANGE) == []
    assert gitops.dirty_outside(repo, f'openspec/changes/{CHANGE}/review') == []


def test_finish_restores_when_summary_commit_fails(repo, tmp_path):
    session = started(repo)
    pass_round(repo, tmp_path, session)
    hook = repo / '.git' / 'hooks' / 'pre-commit'
    hook.write_text('#!/bin/sh\nexit 1\n')
    hook.chmod(0o755)
    before_state = load(repo, 'state.json')
    with pytest.raises(SpecReviewError, match='finish前の状態へ戻しました') as exc:
        finish_mod.finish(session, None, None, confirm=True)
    _assert_rolled_back(repo, exc.value.details['restored_to'], before_state)
    hook.unlink()
    assert finish_mod.finish(session, None, None, confirm=True)['squashed_sha']


def test_finish_never_deletes_preexisting_backup_ref(repo, tmp_path, monkeypatch):
    session = started(repo)
    pass_round(repo, tmp_path, session)
    monkeypatch.setattr(finish_mod, 'stamp_jst', lambda: '20261017-000000')
    ref = f'refs/spec-review/{CHANGE}/20261017-000000'
    git(repo, 'update-ref', ref, 'HEAD')
    with pytest.raises(SpecReviewError, match='既に存在します'):
        finish_mod.finish(session, None, None, confirm=True)
    assert [r['ref'] for r in gitops.list_refs(repo, CHANGE)] == [ref]


def test_rollback_after_ref_creation_failure_keeps_other_refs(repo, tmp_path, monkeypatch):
    session = started(repo)
    pass_round(repo, tmp_path, session)
    other = f'refs/spec-review/{CHANGE}/older'
    git(repo, 'update-ref', other, 'HEAD')

    def failing(root, ref, sha):
        raise RuntimeError('ref failed')

    monkeypatch.setattr(gitops, 'create_ref', failing)
    with pytest.raises(SpecReviewError, match='ref failed'):
        finish_mod.finish(session, None, None, confirm=True)
    assert [r['ref'] for r in gitops.list_refs(repo, CHANGE)] == [other]
    assert load(repo, 'state.json')['status'] != 'finished'
