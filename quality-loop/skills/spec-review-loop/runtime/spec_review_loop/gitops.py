"""Git操作。base固定・round commit・一時worktree・squashと検証・バックアップref。"""
from __future__ import annotations

import contextlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator

from .errors import contract, io_error

DEFAULT_BRANCHES = ('main', 'master')
ROUND_TRAILER = 'Spec-Review-Round'
REF_PREFIX = 'refs/spec-review'


def git(root: Path, *args: str, check: bool = True, input_text: str | None = None) -> str:
    try:
        proc = subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, input=input_text)
    except OSError as exc:
        raise io_error(f'gitを実行できません: {exc}', 'gitが導入されているか確認してください') from exc
    if check and proc.returncode != 0:
        raise io_error(f'git {" ".join(args)} が失敗しました: {proc.stderr.strip()}', 'リポジトリの状態を確認してください')
    return proc.stdout


def toplevel(path: Path) -> Path:
    proc = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=path, capture_output=True, text=True)
    if proc.returncode != 0:
        raise contract(f'Gitリポジトリではありません: {path}', '対象リポジトリで実行するか --root を指定してください')
    return Path(proc.stdout.strip())


def head(root: Path) -> str:
    return git(root, 'rev-parse', 'HEAD').strip()


def current_branch(root: Path) -> str:
    name = git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD', check=False).strip()
    if not name:
        raise contract('detached HEADでは実行できません', 'topic branchへ切り替えてください')
    return name


def ensure_topic_branch(root: Path) -> str:
    branch = current_branch(root)
    if branch in DEFAULT_BRANCHES:
        raise contract(f'{branch} では開始できません', f'topic branchへ切り替えてください（例: git switch -c review/<change-id>）')
    return branch


def status_entries(root: Path) -> list[tuple[str, str]]:
    """(XY, path)の一覧。renameは新pathを返す。"""
    raw = git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    parts = raw.split('\0')
    entries = []
    i = 0
    while i < len(parts):
        item = parts[i]
        i += 1
        if not item:
            continue
        xy, path = item[:2], item[3:]
        if xy[0] in 'RC':
            i += 1  # 元pathを読み飛ばす
        entries.append((xy, path))
    return entries


def _inside(path: str, prefix: str) -> bool:
    prefix = prefix.rstrip('/') + '/'
    return path.startswith(prefix)


def dirty_outside(root: Path, allowed_prefix: str) -> list[str]:
    return [f'{xy} {path}' for xy, path in status_entries(root) if not _inside(path, allowed_prefix)]


def commit_round(root: Path, change_id: str, round_no: int, review_rel: str) -> dict:
    """実装報告を必須とし、stage済み変更とreview/配下だけをcommitする。"""
    report = root / review_rel / f'r{round_no}_report.md'
    if not report.is_file() or not report.read_text(encoding='utf-8').strip():
        raise contract(f'実装報告がありません: {review_rel}/r{round_no}_report.md',
                       '実装内容・検証結果・未対応事項を書いた実装報告を作成してから再実行してください')
    blocked = [f'{xy} {path}' for xy, path in status_entries(root)
               if not _inside(path, review_rel) and (xy == '??' or xy[1] != ' ')]
    if blocked:
        raise contract('unstagedまたはuntrackedの変更があります。対象ならstageし、対象外なら除外してください',
                       '表示されたpathごとに git add するか、作業ツリーから外してから再実行してください',
                       {'paths': blocked})
    git(root, 'add', '--', review_rel)
    staged = [line for line in git(root, 'diff', '--cached', '--name-status').splitlines() if line]
    if not staged:
        raise contract('commitする変更がありません')
    message = f'spec-review: r{round_no} {change_id}\n\n{ROUND_TRAILER}: {change_id} r{round_no}\n'
    git(root, 'commit', '-q', '-F', '-', input_text=message)
    return {'sha': head(root), 'paths': staged}


@contextlib.contextmanager
def review_worktree(root: Path, sha: str) -> Iterator[Path]:
    """round SHAの一時worktreeを作り、成功・失敗・例外のいずれでも削除する。"""
    tmp = Path(tempfile.mkdtemp(prefix='spec-review-'))
    path = tmp / 'wt'
    try:
        git(root, 'worktree', 'add', '--detach', '--quiet', str(path), sha)
        yield path
    finally:
        git(root, 'worktree', 'remove', '--force', str(path), check=False)
        git(root, 'worktree', 'prune', check=False)
        shutil.rmtree(tmp, ignore_errors=True)


def worktree_paths(root: Path) -> list[str]:
    return [line[9:] for line in git(root, 'worktree', 'list', '--porcelain').splitlines() if line.startswith('worktree ')]


def commits_since(root: Path, base: str) -> list[dict]:
    """base..HEADのcommit（古い順）。trailerと親の数を含む。"""
    fmt = f'%H%x1f%P%x1f%s%x1f%(trailers:key={ROUND_TRAILER},valueonly,separator=%x2c)%x1e'
    out = git(root, 'log', '--reverse', f'--format={fmt}', f'{base}..HEAD')
    commits = []
    for record in out.split('\x1e'):
        record = record.strip('\n')
        if not record:
            continue
        sha, parents, subject, trailers = record.split('\x1f')
        commits.append({'sha': sha, 'parents': parents.split(), 'subject': subject,
                        'rounds': [t.strip() for t in trailers.split(',') if t.strip()]})
    return commits


def remote_refs_containing(root: Path, sha: str) -> list[str]:
    out = git(root, 'for-each-ref', '--format=%(refname)', '--contains', sha, 'refs/remotes')
    return [line for line in out.splitlines() if line]


def refs_containing(root: Path, sha: str, exclude_prefix: str = REF_PREFIX) -> list[str]:
    out = git(root, 'for-each-ref', '--format=%(refname)', '--contains', sha)
    return [line for line in out.splitlines() if line and not line.startswith(exclude_prefix + '/')]


def tree_of(root: Path, rev: str) -> str:
    return git(root, 'rev-parse', f'{rev}^{{tree}}').strip()


def backup_ref_name(change_id: str, stamp: str) -> str:
    return f'{REF_PREFIX}/{change_id}/{stamp}'


def create_ref(root: Path, ref: str, sha: str) -> None:
    git(root, 'update-ref', ref, sha, '')  # 既存refがあれば失敗させる


def list_refs(root: Path, change_id: str) -> list[dict]:
    out = git(root, 'for-each-ref', '--format=%(refname) %(objectname)', f'{REF_PREFIX}/{change_id}/')
    return [dict(zip(('ref', 'sha'), line.split(' ', 1))) for line in out.splitlines() if line]


def delete_ref(root: Path, ref: str) -> None:
    git(root, 'update-ref', '-d', ref)


def commit_squash(root: Path, base: str, message: str) -> str:
    """base以降をindexのtreeで1 commitにまとめる。testsでtree不一致を模擬するため分離する。"""
    git(root, 'reset', '--soft', base)
    git(root, 'commit', '-q', '-F', '-', input_text=message)
    return head(root)


def restore(root: Path, backup_sha: str) -> None:
    """HEAD・index・作業ツリーをバックアップへ戻す。

    finishはsquash前に作業ツリーがcleanでバックアップと同じtreeであることを確認しているため、
    ここで捨てるのはsquash処理中に生じた差分だけである。
    """
    git(root, 'reset', '-q', '--hard', backup_sha)
    if git(root, 'status', '--porcelain', '--untracked-files=no').strip():
        raise io_error('バックアップへの復元後も差分が残っています', 'git status を確認してください')
