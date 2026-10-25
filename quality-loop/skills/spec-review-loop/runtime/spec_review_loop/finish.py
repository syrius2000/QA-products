"""finish（検証付きsquash）とprune（バックアップref削除）。"""
from __future__ import annotations

import re

from . import gitops, report
from .gate import OPEN_STATUSES, latest_review
from .errors import contract, io_error
from .session import Session, now_jst, stamp_jst


def default_message(session: Session) -> str:
    """件名の既定値: feat(<change-id>): <proposalの最初の本文行>。"""
    path = session.change_dir / 'proposal.md'
    first = ''
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            text = line.strip()
            if text and not text.startswith('#'):
                first = re.split(r'[。．.]', re.sub(r'[`*]', '', text), maxsplit=1)[0]
                break
    return f'feat({session.change_id}): {first[:60] or "spec-review完了"}'


def _reviewer_label(record: dict) -> str:
    r = record.get('reviewer') or {}
    return f'{r.get("tool", "unknown")} {r.get("version", "unknown")} / {r.get("model", "unknown")}'


def plan(session: Session, message: str | None, accept_residual: str | None) -> dict:
    """前提条件を検査し、squash計画を返す。何も変更しない。"""
    state = session.state()
    if state['status'] == 'finished':
        raise contract('このループはsquash済みです')
    session.require_integrity(state)
    session.assert_no_review_running()  # lock_infoの内容ではなくOSロックで判断する（取得直後でPID未記入でも検知できる）
    reviewed = [r for r in state['rounds'] if r.get('gate') is not None]
    if not reviewed or reviewed[-1] is not state['rounds'][-1]:
        raise contract('レビュー済みのroundがありません', 'commit-round と review を先に実行してください')
    last = state['rounds'][-1]
    gate_value = last['gate']['gate']
    if gate_value != 'PASS' and not (accept_residual or '').strip():
        raise contract(f'最終GateがPASSではありません（{gate_value}）',
                       'PASS以外で終了するなら、利用者の判断を --accept-residual "<判断>" で明示してください')
    unconsumed = [i for i in state.get('instructions', []) if i['consumed_round'] is None]
    if unconsumed and not (accept_residual or '').strip():
        raise contract('実装報告に反映されていない人の指示があります',
                       '指示を反映する場合はループを続けてください。反映せずに終了する場合は、利用者の判断を --accept-residual "<判断>" で明示してください',
                       {'instructions': [f'{i["id"]}: {i["text"]}' for i in unconsumed]})
    if gitops.current_branch(session.root) != state['branch']:
        raise contract(f'開始時のbranch {state["branch"]} ではありません')
    commits = gitops.commits_since(session.root, state['base_sha'])
    if not commits:
        raise contract('base以降にcommitがありません')
    foreign = [c for c in commits if len(c['parents']) != 1
               or not any(t.startswith(f'{session.change_id} r') for t in c['rounds'])]
    if foreign:
        raise contract('base..HEADにこのchangeのround commit以外が含まれています',
                       '他の作業のcommitを別branchへ移してから再実行してください',
                       {'commits': [f'{c["sha"][:12]} {c["subject"]}' for c in foreign]})
    reviewed_shas = [r['sha'] for r in state['rounds']]
    if [c['sha'] for c in commits] != reviewed_shas:
        raise contract('base..HEADのcommitがレビュー済みのround commitと一致しません（round commitの書換え・追加の可能性）',
                       'レビュー済みのcommitへ戻すか、新しいroundとして commit-round と review をやり直してください',
                       {'expected': [sha[:12] for sha in reviewed_shas], 'actual': [c['sha'][:12] for c in commits]})
    pushed = {c['sha']: gitops.remote_refs_containing(session.root, c['sha']) for c in commits}
    pushed = {sha: refs for sha, refs in pushed.items() if refs}
    if pushed:
        raise contract('round commitが既にリモートへpushされています。squashにはforce-pushが必要になるため実行しません',
                       'squashするには別途の明示承認と手作業が必要です。squashせずにそのまま残すこともできます',
                       {'pushed': {sha[:12]: refs for sha, refs in pushed.items()}})
    dirty = gitops.dirty_outside(session.root, session.review_rel)
    if dirty:
        raise contract('作業ツリーまたはindexがcleanではありません', 'commitするか退避してから再実行してください', {'paths': dirty})
    subject = (message or default_message(session)).strip()
    trailers = [f'Spec-Review: {session.change_id}', f'Spec-Review-Gate: {gate_value}',
                f'Spec-Review-Rounds: {len(state["rounds"])}', f'Spec-Review-Reviewer: {_reviewer_label(last)}',
                f'Spec-Review-Pre-Squash: {last["sha"]}']
    if unconsumed:
        trailers.append('Spec-Review-Unconsumed-Instructions: ' + ', '.join(i['id'] for i in unconsumed))
        trailers.append('Spec-Review-Unconsumed-Judgment: ' + ' '.join(accept_residual.split()))
    if gate_value != 'PASS':
        _, latest = latest_review(state['rounds'])
        residual = [f['id'] for f in (latest or {}).get('findings', []) if f['status'] in OPEN_STATUSES]
        trailers.append('Spec-Review-Residual: ' + ' '.join(accept_residual.split()))
        trailers.append('Spec-Review-Residual-Findings: ' + (', '.join(residual) or 'なし'))
    return {
        'dry_run': True, 'base_sha': state['base_sha'], 'gate': gate_value,
        'commits': [f'{c["sha"][:12]} {c["subject"]}' for c in commits],
        'pending_review_files': [f'{xy} {path}' for xy, path in gitops.status_entries(session.root)
                                 if path.startswith(session.review_rel + '/')],
        'backup_ref': gitops.backup_ref_name(session.change_id, stamp_jst()),
        'message': subject + '\n\n' + '\n'.join(trailers) + '\n', 'accept_residual': accept_residual,
    }


def finish(session: Session, message: str | None, accept_residual: str | None, confirm: bool) -> dict:
    if not confirm:
        with session.state_lock():
            return plan(session, message, accept_residual)
    # 前提条件の検査から`finished`の確定までを、状態ロックを保持したまま行う。
    # 検査後に別プロセスが`instruct`などで状態を変えて、検査と矛盾した状態で終了することを防ぐ。
    with session.state_lock():
        p = plan(session, message, accept_residual)
        session.assert_no_review_running()
        state = session.state()
        last = state['rounds'][-1]
        pre_head = gitops.head(session.root)
        info = {'at': now_jst(), 'backup_ref': p['backup_ref'], 'pre_squash_sha': last['sha'],
                'gate': p['gate'], 'accept_residual': accept_residual, 'squash': 'pending'}
        if any(r['ref'] == p['backup_ref'] for r in gitops.list_refs(session.root, session.change_id)):
            raise contract(f'バックアップref {p["backup_ref"]} が既に存在します', '1秒以上おいて finish を再実行してください')
        backup = None
        ref_created = False
        try:
            session.write_text('summary.md', report.summary_markdown(state, info))
            session.write_json('state.json', {**state, 'status': 'finished', 'finish': info})
            gitops.git(session.root, 'add', '--', session.review_rel)
            n = last['round']
            gitops.git(session.root, 'commit', '-q', '-F', '-', input_text=(
                f'spec-review: r{n} {session.change_id} summary\n\n{gitops.ROUND_TRAILER}: {session.change_id} r{n}-summary\n'))
            if gitops.status_entries(session.root):
                raise io_error('summary commit後も作業ツリーがcleanではありません')
            backup = gitops.head(session.root)
            gitops.create_ref(session.root, p['backup_ref'], backup)
            ref_created = True
            squashed = gitops.commit_squash(session.root, p['base_sha'], p['message'])
            expected, actual = gitops.tree_of(session.root, p['backup_ref']), gitops.tree_of(session.root, 'HEAD')
            if expected != actual:
                raise io_error('squash後のtreeがsquash前と一致しません', details={'expected_tree': expected, 'actual_tree': actual})
        except Exception as exc:
            _rollback(session, state, pre_head, backup, p['backup_ref'] if ref_created else None)
            details = {**getattr(exc, 'details', {}), 'restored_to': pre_head}
            raise io_error(f'finishに失敗したため、finish前の状態へ戻しました: {getattr(exc, "message", exc)}',
                           '原因を調査してから finish を再実行してください', details) from exc
    return {**p, 'dry_run': False, 'squashed_sha': squashed, 'backup_sha': backup, 'tree': actual}


def _rollback(session: Session, pre_state: dict, pre_head: str, backup: str | None, created_ref: str | None) -> None:
    """finish前の状態（最終round commit＋未commitのreview成果物、終了前のstate）へ戻す。

    finishの前提条件により、review/以外の作業ツリーはcleanで、HEADと同じtreeである。
    """
    if backup is not None:
        gitops.restore(session.root, backup)                # summary commitの状態へ完全に戻す
    gitops.git(session.root, 'reset', '-q', pre_head)       # summary commitを外し、review成果物を未commitへ
    session.write_json('state.json', pre_state)
    session.path('summary.md').unlink(missing_ok=True)
    if created_ref is not None:
        gitops.delete_ref(session.root, created_ref)        # 今回作ったrefだけを消す。round commitはbranchから到達できる


def prune(session: Session, confirm: bool) -> dict:
    """バックアップrefと、削除で到達不能になるround SHAを示し、確認後にだけ削除する。"""
    refs = gitops.list_refs(session.root, session.change_id)
    if not refs:
        raise contract(f'{gitops.REF_PREFIX}/{session.change_id}/ にバックアップrefがありません')
    state = session.state()
    candidates = [r['sha'] for r in state['rounds']] + [r['sha'] for r in refs]
    unreachable = sorted({sha for sha in candidates if not gitops.refs_containing(session.root, sha)})
    result = {'refs': refs, 'unreachable_after_prune': unreachable, 'deleted': [], 'dry_run': not confirm}
    if not confirm:
        return result
    for r in refs:
        gitops.delete_ref(session.root, r['ref'])
    return {**result, 'deleted': [r['ref'] for r in refs]}
