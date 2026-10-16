"""spec-review-loop CLI。決定論的な部分だけを担い、実装とFinding対応はSkillの手順で行う。"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from . import finish as finish_mod
from . import review_round, reviewers
from .render import render_text
from .errors import EXIT_INTERNAL, EXIT_IO, EXIT_OK, SpecReviewError
from .session import Session


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='spec-review-loop-cli', description='OpenSpec changeを受入基準とする独立レビューループ')
    p.add_argument('--root', type=Path, default=Path.cwd(), help='対象リポジトリ（既定: 現在の作業DIR）')
    p.add_argument('--json', action='store_true', help='JSONで出力する')
    sub = p.add_subparsers(dest='operation', required=True)
    s = sub.add_parser('start', help='基準を抽出・固定し、base SHAを記録する')
    s.add_argument('change_id')
    s.add_argument('--reviewer', choices=sorted(reviewers.ADAPTERS))
    s.add_argument('--max-rounds', type=int)
    s.add_argument('--model')
    s.add_argument('--timeout', type=int, help='Reviewerのtimeout秒')
    s.add_argument('--effort', help='Reviewerの推論effort（codexは-c model_reasoning_effort、claudeは--effort、cursorはmodel[effort=…]）')
    sub.add_parser('commit-round', help='実装報告付きのround commitを作る').add_argument('change_id')
    r = sub.add_parser('review', help='round SHAを別系統のReviewerで読取り専用レビューする')
    r.add_argument('change_id')
    r.add_argument('--reviewer', choices=sorted(reviewers.ADAPTERS))
    r.add_argument('--model')
    r.add_argument('--timeout', type=int)
    r.add_argument('--effort')
    sub.add_parser('status', help='状態と次の操作を表示する（読取りのみ）').add_argument('change_id')
    f = sub.add_parser('finish', help='round commit群を検証付きで1 commitへsquashする（既定はdry-run）')
    f.add_argument('change_id')
    f.add_argument('--confirm', action='store_true', help='計画を確認したうえで実行する')
    f.add_argument('--message', help='squash commitの件名')
    f.add_argument('--accept-residual', help='PASS以外で終了する場合の利用者の判断')
    pr = sub.add_parser('prune', help='バックアップrefを削除する（既定は表示のみ）')
    pr.add_argument('change_id')
    pr.add_argument('--confirm', action='store_true')
    rf = sub.add_parser('refreeze', help='利用者の明示指示で受入基準を再固定する')
    rf.add_argument('change_id')
    rf.add_argument('--reason', required=True, help='利用者の指示内容')
    d = sub.add_parser('doctor', help='git・openspec・Reviewer CLIの版と必要フラグを確認する')
    d.add_argument('--reviewer', choices=sorted(reviewers.ADAPTERS), default=reviewers.DEFAULT_REVIEWER)
    return p


def doctor(selected: str) -> tuple[dict, int]:
    tools = {}
    for name, argv in (('git', ['git', '--version']), ('openspec', ['openspec', '--version'])):
        exe = shutil.which(name)
        version = subprocess.run(argv, capture_output=True, text=True).stdout.strip() if exe else None
        tools[name] = {'path': exe, 'version': version, 'ok': bool(exe)}
    probes = {name: reviewers.probe(name) for name in reviewers.ADAPTERS}
    ok = tools['git']['ok'] and probes[selected]['ok']
    return {'tools': tools, 'reviewers': probes, 'selected': selected, 'ok': ok}, (EXIT_OK if ok else 2)


def execute(a) -> tuple[dict, int]:
    if a.operation == 'doctor':
        return doctor(a.reviewer)
    session = Session(a.root, a.change_id)
    op = a.operation
    if op == 'start':
        return session.start(a.reviewer, a.max_rounds, a.model, a.timeout, a.effort), EXIT_OK
    if op == 'commit-round':
        return session.commit_round(), EXIT_OK
    if op == 'review':
        result = review_round.review(session, a.reviewer, a.model, a.timeout, a.effort)
        return result, (EXIT_IO if result['reviewer_failed'] else EXIT_OK)
    if op == 'status':
        return session.status(), EXIT_OK
    if op == 'finish':
        return finish_mod.finish(session, a.message, a.accept_residual, a.confirm), EXIT_OK
    if op == 'prune':
        return finish_mod.prune(session, a.confirm), EXIT_OK
    if op == 'refreeze':
        return session.refreeze(a.reason), EXIT_OK
    raise SpecReviewError('未定義の操作です', exit_code=EXIT_INTERNAL)


def main(argv: list[str] | None = None) -> int:
    a = parser().parse_args(argv)
    change_id = getattr(a, 'change_id', None)
    try:
        result, code = execute(a)
    except SpecReviewError as exc:
        result, code = exc.as_result(), exc.exit_code
    except Exception as exc:  # noqa: BLE001 - 想定外は内部エラーとして理由を残す
        result, code = {'status': 'error', 'message': f'内部エラー: {type(exc).__name__}: {exc}',
                        'action': '入力と状態を保存し、実装者へ調査を依頼してください', 'details': {}}, EXIT_INTERNAL
    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(a.operation, result, change_id))
    return code


if __name__ == '__main__':
    sys.exit(main())
