"""ループの状態（review/state.json）と、start・commit-round・refreeze・status。"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import criteria as crit
from . import gitops, reviewers
from .errors import contract, io_error
from .gate import DEFAULT_MAX_ROUNDS

JST = timezone(timedelta(hours=9))
LOCK_NAME = '.review.lock'
STATE_LOCK_NAME = '.state.lock'
GITIGNORE_LINES = ('*.log', LOCK_NAME, STATE_LOCK_NAME, '*.tmp')


def now_jst() -> str:
    return datetime.now(JST).isoformat(timespec='seconds')


def stamp_jst() -> str:
    return datetime.now(JST).strftime('%Y%m%d-%H%M%S')


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # 終了したが回収されていない（ゾンビ）プロセスは、実行中とみなさない（Linuxのみ確認できる）
    try:
        return Path(f'/proc/{pid}/stat').read_text(encoding='utf-8').rsplit(')', 1)[1].split()[0] != 'Z'
    except (OSError, IndexError):
        return True


def _read_lock_fd(fd: int) -> dict:
    """ロックファイルの内容（JSON）を読む。空・壊れている場合は空の辞書。"""
    os.lseek(fd, 0, os.SEEK_SET)
    try:
        value = json.loads(os.read(fd, 1 << 16).decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _reviewer_alive(info: dict) -> bool:
    """記録された子Reviewerが生きているか。親CLIの状態とは独立に判断する。"""
    rp = info.get('reviewer_pid')
    return bool(rp) and pid_alive(int(rp))


class Session:
    """1つのchangeに対するループ。state.json・成果物の入出力と、それを守る排他ロック・実行中情報・SHA-256による改ざん検知を持つ。"""

    def __init__(self, root: Path, change_id: str):
        self.root = gitops.toplevel(root)
        self.change_id = change_id
        self.change_dir = crit.change_dir(self.root, change_id)
        self.review_dir = self.change_dir / 'review'
        self.review_rel = self.review_dir.relative_to(self.root).as_posix()
        self.change_rel = self.change_dir.relative_to(self.root).as_posix()

    # --- 入出力 ---
    def path(self, name: str) -> Path:
        return self.review_dir / name

    def read_json(self, name: str) -> dict:
        try:
            return json.loads(self.path(name).read_text(encoding='utf-8'))
        except FileNotFoundError as exc:
            raise contract(f'{self.review_rel}/{name} がありません', f'先に start を実行してください（spec-review-loop-cli start {self.change_id}）') from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise io_error(f'{self.review_rel}/{name} を読めません: {exc}') from exc

    def write_json(self, name: str, data: dict) -> None:
        self.review_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.path(f'{name}.{os.getpid()}.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(tmp, self.path(name))  # 読み手が書きかけを見ないよう、原子的に置き換える

    @contextlib.contextmanager
    def state_lock(self):
        """state.jsonの読取り→更新→保存を直列化する排他ロック（OSのファイルロック。プロセスが死ねば解放される）。"""
        self.ensure_gitignore()
        fd = os.open(self.path(STATE_LOCK_NAME), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def write_text(self, name: str, text: str) -> None:
        self.review_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.path(f'{name}.{os.getpid()}.tmp')
        tmp.write_text(text, encoding='utf-8')
        os.replace(tmp, self.path(name))  # 読み手が書きかけを見ないよう、原子的に置き換える

    def record_prompt(self, round_no: int, prompt: str) -> str:
        """Reviewerへ渡すプロンプトを保存し、記録（SHA-256）を同じ状態ロックの下で更新する。

        attempt番号は、記録済みattemptと保存済みプロンプトの最大番号から採番する。親CLIが異常終了して
        attemptが記録されなかった場合も、前のattemptのプロンプトとハッシュを上書きしない。"""
        sha = sha256_text(prompt)
        with self.state_lock():
            state = self.state()
            index = next(k for k, r in enumerate(state['rounds']) if r['round'] == round_no)
            record = state['rounds'][index]
            existing = record.get('prompt_files', {})
            attempt_no = max([len(record.get('attempts', [])), *(int(k) for k in existing)]) + 1
            attempt_name = f'r{round_no}_prompt.attempt{attempt_no}.md'
            self.write_text(attempt_name, prompt)
            self.write_text(f'r{round_no}_prompt.md', prompt)
            files = {**existing, str(attempt_no): {'file': attempt_name, 'sha256': sha}}
            record = {**record, 'prompt_sha256': sha, 'prompt_files': files}
            rounds = [*state['rounds'][:index], record, *state['rounds'][index + 1:]]
            self.write_json('state.json', {**state, 'rounds': rounds})
        return sha

    def state(self) -> dict:
        return self.read_json('state.json')

    def frozen(self) -> dict:
        return self.read_json('criteria.json')

    def config(self) -> dict:
        path = self.path('config.json')
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            raise contract(f'{self.review_rel}/config.json を読めません: {exc}') from exc
        return data if isinstance(data, dict) else {}

    # --- 実行中ロック・ログ（review実行中の進行確認） ---
    def ensure_gitignore(self) -> None:
        self.review_dir.mkdir(parents=True, exist_ok=True)
        path = self.path('.gitignore')
        have = path.read_text(encoding='utf-8').splitlines() if path.exists() else []
        missing = [line for line in GITIGNORE_LINES if line not in have]
        if missing:
            path.write_text('\n'.join([*have, *missing]) + '\n', encoding='utf-8')

    def lock_info(self) -> dict | None:
        """実行中のreviewの情報（表示・拒否の判断用）。排他の正本はacquire_lockのOSロックで、これは参考情報。

        親CLIが生きている間、または親CLIが異常終了しても子Reviewerが生きている間は情報を返す。
        どちらも終了していれば（内容が空を含む）Noneを返す。
        """
        try:
            info = json.loads(self.path(LOCK_NAME).read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(info, dict):
            return None
        if pid_alive(int(info.get('pid', 0))) or _reviewer_alive(info):
            return info
        return None

    def acquire_lock(self, round_no: int, tool: str) -> None:
        """OSのファイルロックで排他する。親CLIが死んでもOSが解放するが、記録された子Reviewerが生きていれば開始しない。"""
        self.ensure_gitignore()
        fd = os.open(self.path(LOCK_NAME), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            info = self.lock_info() or {}
            raise contract(f'r{info.get("round", "?")}のレビューが実行中です（PID {info.get("pid", "不明")}、{info.get("tool", "")}）',
                           f'status で進行を確認してください（{self.review_rel}/r{info.get("round", "<N>")}_reviewer.log）。終了を待ってから再実行します',
                           {'lock': info})
        prev = _read_lock_fd(fd)  # 前回の親CLIが異常終了していた場合の残り
        if _reviewer_alive(prev):
            os.close(fd)
            raise contract(f'前回のReviewer（PID {prev["reviewer_pid"]}、r{prev.get("round", "?")} {prev.get("tool", "")}）がまだ実行中です（親CLIは終了しています）',
                           f'status で進行を確認し、終了を待ってから再実行してください（{self.review_rel}/r{prev.get("round", "<N>")}_reviewer.log）',
                           {'lock': prev})
        self._lock_fd = fd
        self._lock_info = {'pid': os.getpid(), 'round': round_no, 'tool': tool, 'started_at': now_jst(),
                           'started_epoch': datetime.now(JST).timestamp()}
        self._write_lock_info()

    def update_lock_info(self, round_no: int, tool: str) -> None:
        """保持中のロックの表示用情報を、再読込後のround・toolへ更新する（排他には影響しない）。"""
        if getattr(self, '_lock_fd', None) is None:
            return
        self._lock_info = {**getattr(self, '_lock_info', {}), 'round': round_no, 'tool': tool, 'started_at': now_jst(),
                           'started_epoch': datetime.now(JST).timestamp()}
        self._write_lock_info()

    def set_reviewer_pid(self, pid: int) -> None:
        """子Reviewerのプロセスを記録する。親CLIが死んでも、この記録で実行中かどうかを判断できる。"""
        if getattr(self, '_lock_fd', None) is None:
            return
        self._lock_info = {**getattr(self, '_lock_info', {}), 'reviewer_pid': pid}
        self._write_lock_info()

    def _write_lock_info(self) -> None:
        fd = self._lock_fd
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, json.dumps(self._lock_info).encode('utf-8'))

    def release_lock(self) -> None:
        fd = getattr(self, '_lock_fd', None)
        if fd is None:
            return
        self._lock_fd = None
        try:
            # 子Reviewerが残っている間は記録を消さず、親CLIが終わった後も実行中と分かるようにする
            if not _reviewer_alive(getattr(self, '_lock_info', {})):
                os.ftruncate(fd, 0)  # 内容を空にしてから解放する（空は「実行中でない」）
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def reviewing(self) -> dict | None:
        info = self.lock_info()
        if not info:
            return None
        log = self.path(f'r{info.get("round")}_reviewer.log')
        tail = log.read_text(encoding='utf-8', errors='replace').splitlines()[-20:] if log.exists() else []
        return {**{k: info.get(k) for k in ('pid', 'round', 'tool', 'started_at', 'reviewer_pid')},
                'elapsed_seconds': int(datetime.now(JST).timestamp() - info.get('started_epoch', 0)),
                'log': f'{self.review_rel}/r{info.get("round")}_reviewer.log', 'log_tail': tail}

    # --- 保存した成果物の改ざん検知 ---
    def integrity_problems(self, state: dict | None = None) -> list[str]:
        state = state or self.state()
        problems = []
        for record in state['rounds']:
            n = record['round']
            for key, name in (('review_sha256', f'r{n}_review.json'), ('prompt_sha256', f'r{n}_prompt.md')):
                want = record.get(key)
                if want and (not self.path(name).exists() or sha256_file(self.path(name)) != want):
                    problems.append(f'{self.review_rel}/{name}')
            for entry in record.get('prompt_files', {}).values():
                if not self.path(entry['file']).exists() or sha256_file(self.path(entry['file'])) != entry['sha256']:
                    problems.append(f'{self.review_rel}/{entry["file"]}')
        return problems

    def require_integrity(self, state: dict) -> None:
        problems = self.integrity_problems(state)
        if problems:
            raise contract('HOLD: 記録したSHA-256と一致しないレビュー成果物があります（保存後に書き換えられた可能性）',
                           '改変の経緯を確認し、元に戻すか、新しいroundとしてやり直してください', {'files': problems})

    # --- instruct ---
    def instruct(self, message: str | None) -> dict:
        if not (message or '').strip():
            raise contract('instructには人の発言（--message）が必要です', '利用者の実際の発言を原文のまま渡してください')
        with self.state_lock():
            state = self.state()
            if state['status'] != 'active':
                label = {'finished': '終了済み', 'stopped': f'停止中（{state.get("stop_reason")}）'}.get(state['status'], state['status'])
                raise contract(f'ループが{label}のため、指示を次のroundへ引き継げません',
                               'HOLDで停止している場合は、利用者の指示で refreeze してから指示を記録してください。'
                               'PASSなどで終える場合は、新しい指示を扱うか、finish --accept-residual で判断を明示してください')
            after = state['rounds'][-1]['round'] if state['rounds'] else 0
            items = state.get('instructions', [])
            entry = {'id': f'I-{len(items) + 1:03d}', 'at': now_jst(), 'text': message.strip(),
                     'after_round': after, 'consumed_round': None}
            self.write_json('state.json', {**state, 'instructions': [*items, entry], 'awaiting_user': False})
        return {'instruction': entry, 'next': f'次のr{after + 1}_report.mdに指示の原文を含めて実装し、commit-round を実行してください'}

    # --- start ---
    def start(self, reviewer: str | None, max_rounds: int | None, model: str | None, timeout: int | None,
              effort: str | None = None, pause: str | None = None) -> dict:
        branch = gitops.ensure_topic_branch(self.root)
        if self.path('state.json').exists():
            raise contract('このchangeのレビューループは開始済みです', 'status で現在の状態を確認してください')
        dirty = gitops.dirty_outside(self.root, self.change_rel)
        if dirty:
            raise contract('対象change以外に未commitの変更があります', 'commitするか別worktreeへ移してから再実行してください', {'paths': dirty})
        cfg = self.config()
        options = {
            'reviewer': reviewer or cfg.get('reviewer') or reviewers.DEFAULT_REVIEWER,
            'model': model or cfg.get('model'),
            'effort': effort or cfg.get('effort'),
            'timeout': timeout or cfg.get('timeout') or reviewers.DEFAULT_TIMEOUT,
            'max_rounds': max_rounds or cfg.get('max_rounds') or DEFAULT_MAX_ROUNDS,
            'pause': pause or cfg.get('pause') or 'none',
        }
        if options['pause'] not in ('none', 'round'):
            raise contract('pauseは none か round を指定してください')
        reviewers.get(options['reviewer'])
        if options['effort'] is not None and not re.fullmatch(r'[a-z]+', str(options['effort'])):
            raise contract('effortは英小文字で指定してください（例: low／medium／high）')
        if not isinstance(options['max_rounds'], int) or options['max_rounds'] < 1:
            raise contract('round上限は1以上の整数で指定してください')
        doc = crit.build(self.root, self.change_id)
        state = {
            'schema_version': 1, 'change_id': self.change_id, 'branch': branch,
            'base_sha': gitops.head(self.root), 'started_at': now_jst(), 'status': 'active',
            'max_rounds': options['max_rounds'], 'reviewer': options['reviewer'], 'model': options['model'], 'effort': options['effort'],
            'timeout': options['timeout'], 'rounds': [], 'refreezes': [], 'finish': None,
            'pause': options['pause'], 'awaiting_user': False, 'instructions': [],
        }
        self.write_json('criteria.json', {**doc, 'frozen_at': now_jst()})
        self.write_json('state.json', state)
        self.ensure_gitignore()
        probe = reviewers.probe(options['reviewer'])
        return {'state': state, 'criteria': doc, 'reviewer_probe': probe,
                'pending_change_files': gitops.dirty_outside(self.root, self.review_rel)}

    # --- commit-round ---
    def next_round(self, state: dict) -> int:
        if state['status'] != 'active':
            label = {'stopped': '停止しています', 'finished': '終了しています'}.get(state['status'], state['status'])
            raise contract(f'ループは{label}（理由: {state.get("stop_reason")}）', 'status で次の操作を確認してください')
        if not state['rounds']:
            return 1
        last = state['rounds'][-1]
        if last.get('gate') is None or last.get('retry_allowed'):
            raise contract(f'r{last["round"]}のレビューが完了していません', 'review を実行してください')
        if last['stop']['stop'] and not self._refrozen_after(state, last['round']):
            raise contract(f'ループは停止しています（{last["stop"]["reason"]}）', 'status で引継ぎの選択肢を確認してください')
        return last['round'] + 1

    @staticmethod
    def _refrozen_after(state: dict, round_no: int) -> bool:
        return any(r['after_round'] == round_no for r in state.get('refreezes', []))

    def drift_against_worktree(self) -> dict:
        return crit.drift(self.frozen(), crit.build(self.root, self.change_id, allow_empty=True))

    def assert_no_review_running(self) -> None:
        """state.lockを保持したまま呼ぶ。reviewのflockを一時的に取り、取れなければ実行中。
        flockが取れても、記録された子Reviewerが生きていれば（親CLIが異常終了した後でも）実行中とみなす。"""
        self.ensure_gitignore()
        fd = os.open(self.path(LOCK_NAME), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                info = self.lock_info() or {}
                raise contract(f'r{info.get("round", "?")}のレビューが実行中です（PID {info.get("pid", "不明")}）',
                               f'status で進行を確認し、終了を待ってください') from exc
            prev = _read_lock_fd(fd)
            if _reviewer_alive(prev):
                raise contract(f'前回のReviewer（PID {prev["reviewer_pid"]}）がまだ実行中です（親CLIは終了しています）',
                               'status で進行を確認し、終了を待ってください')
        finally:
            os.close(fd)  # closeでflockも解放される

    def commit_round(self) -> dict:
        # 検証から書込みまでを状態ロックで囲み、確認後に別プロセスが状態を変えられないようにする
        with self.state_lock():
            state = self.state()
            if gitops.current_branch(self.root) != state['branch']:
                raise contract(f'開始時のbranch {state["branch"]} ではありません', f'git switch {state["branch"]} で戻ってください')
            self.require_integrity(state)
            self.assert_no_review_running()
            if state.get('awaiting_user'):
                raise contract('一時停止中です（--pause round）。結果を人に見せ、指示を受けてから進めます',
                               f'人の発言を spec-review-loop-cli instruct {self.change_id} --message "<発言>" で記録してください')
            round_no = self.next_round(state)
            if round_no > state['max_rounds']:
                raise contract('round上限に達しています', 'status で引継ぎの選択肢を確認してください')
            diff = self.drift_against_worktree()
            if crit.has_drift(diff):
                raise contract('基準ドリフト（HOLD）: 固定した受入基準が変更されています', '意図した変更なら利用者の明示指示で refreeze を実行してください', {'drift': diff})
            pending = [i for i in state.get('instructions', []) if i['consumed_round'] is None]
            if pending:
                report_path = self.path(f'r{round_no}_report.md')
                body = report_path.read_text(encoding='utf-8') if report_path.exists() else ''
                missing = [i for i in pending if i['text'] not in body]
                if missing:
                    raise contract('人の指示が実装報告に転記されていません',
                                   f'{self.review_rel}/r{round_no}_report.md に次の指示を原文のまま記載し、対応内容を書いてください',
                                   {'instructions': [f'{i["id"]}: {i["text"]}' for i in missing]})
            result = gitops.commit_round(self.root, self.change_id, round_no, self.review_rel)
            record = {'round': round_no, 'sha': result['sha'], 'committed_at': now_jst(), 'attempts': [],
                      'gate': None, 'stop': None, 'review': None, 'retry_allowed': False}
            consumed = {i['id'] for i in pending}
            instructions = [{**i, 'consumed_round': round_no} if i['id'] in consumed else i
                            for i in state.get('instructions', [])]
            self.write_json('state.json', {**state, 'rounds': [*state['rounds'], record], 'instructions': instructions})
        return {'round': round_no, 'sha': result['sha'], 'paths': result['paths']}

    # --- refreeze ---
    def refreeze(self, reason: str) -> dict:
        if not reason.strip():
            raise contract('refreezeには利用者の指示内容（--reason）が必要です')
        with self.state_lock():
            state = self.state()
            if state['status'] == 'finished':
                raise contract('終了済みのループは再固定できません')
            doc = crit.build(self.root, self.change_id)
            diff = crit.drift(self.frozen(), doc)
            after = state['rounds'][-1]['round'] if state['rounds'] else 0
            entry = {'at': now_jst(), 'reason': reason, 'after_round': after, 'drift': diff, 'fingerprint': doc['fingerprint']}
            reopen = state['status'] == 'stopped' and state.get('stop_reason') == 'hold'
            new_state = {**state, 'refreezes': [*state.get('refreezes', []), entry],
                         'status': 'active' if reopen else state['status'],
                         'stop_reason': None if reopen else state.get('stop_reason')}
            self.write_json('criteria.json', {**doc, 'frozen_at': now_jst()})
            self.write_json('state.json', new_state)
        return {'drift': diff, 'criteria': doc, 'reopened': reopen}

    # --- status ---
    def status(self) -> dict:
        with self.state_lock():  # 保存中のファイルと記録の食い違いを、誤って改ざんと判定しない
            state = self.state()
            problems = self.integrity_problems(state)
        running = self.reviewing()
        nxt = next_action(state, self.change_id)
        if problems:
            nxt = 'HOLD: 記録したSHA-256と一致しない成果物があります（' + ', '.join(problems) + '）。改変の経緯を確認してください'
        elif running:
            nxt = f'r{running["round"]}のレビューが実行中です。ログ（{running["log"]}）を確認し、終了を待ってください'
        return {'state': state, 'next': nxt, 'reviewing': running, 'integrity_problems': problems}


def next_action(state: dict, change_id: str) -> str:
    cli = 'spec-review-loop-cli'
    if state['status'] == 'finished':
        return f'squash済みです。openspec archive {change_id} の実行は利用者が判断してください'
    if state['status'] == 'stopped':
        reason = state.get('stop_reason')
        if reason == 'pass':
            return f'GateはPASSです。{cli} finish {change_id} で計画を確認し、--confirm でsquashしてください。archiveは利用者が判断します'
        if reason == 'hold':
            return f'HOLDで中断しています。原因を解消するか、利用者の明示指示で {cli} refreeze {change_id} --reason "..." を実行してください'
        return ('PASS以外で停止しました。残ったFindingを確認し、人の判断・quality-reviewのreview-standalone・blind-qa-cycleのいずれかへ引き継いでください。'
                f'終了する場合は {cli} finish {change_id} --accept-residual "<判断>" を使います')
    if not state['rounds']:
        return f'実装して {state_review_rel(change_id)}/r1_report.md を書き、対象をstageして {cli} commit-round {change_id} を実行してください'
    last = state['rounds'][-1]
    if last.get('gate') is None or last.get('retry_allowed'):
        return f'{cli} review {change_id} でr{last["round"]}のレビューを実行してください'
    if last.get('review') is None and last['gate']['gate'] == 'INCONCLUSIVE':
        tried = sorted({a['tool'] for a in last.get('attempts', [])})
        return (f'r{last["round"]}のReviewerが失敗しました（試行済み: {", ".join(tried)}）。'
                f'未試行のReviewerなら {cli} review {change_id} --reviewer <別のReviewer> で再実行できます')
    if state.get('awaiting_user'):
        return (f'一時停止中（--pause round）です。r{last["round"]}の結果を人に見せ、人の発言を '
                f'{cli} instruct {change_id} --message "<発言>" で記録してから進めてください')
    n = last['round'] + 1
    return f'Findingに対応し、{state_review_rel(change_id)}/r{n}_report.md を書いてstageし、{cli} commit-round {change_id} を実行してください'


def state_review_rel(change_id: str) -> str:
    return f'openspec/changes/{change_id}/review'
