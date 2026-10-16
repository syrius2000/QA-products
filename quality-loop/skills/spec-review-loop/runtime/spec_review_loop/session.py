"""ループの状態（review/state.json）と、start・commit-round・refreeze・status。"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import criteria as crit
from . import gitops, reviewers
from .errors import contract, io_error
from .gate import DEFAULT_MAX_ROUNDS

JST = timezone(timedelta(hours=9))


def now_jst() -> str:
    return datetime.now(JST).isoformat(timespec='seconds')


def stamp_jst() -> str:
    return datetime.now(JST).strftime('%Y%m%d-%H%M%S')


class Session:
    """1つのchangeに対するループ。pathとJSON入出力だけを持つ。"""

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
        self.path(name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def write_text(self, name: str, text: str) -> None:
        self.review_dir.mkdir(parents=True, exist_ok=True)
        self.path(name).write_text(text, encoding='utf-8')

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

    # --- start ---
    def start(self, reviewer: str | None, max_rounds: int | None, model: str | None, timeout: int | None,
              effort: str | None = None) -> dict:
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
        }
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
        }
        self.write_json('criteria.json', {**doc, 'frozen_at': now_jst()})
        self.write_json('state.json', state)
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

    def commit_round(self) -> dict:
        state = self.state()
        if gitops.current_branch(self.root) != state['branch']:
            raise contract(f'開始時のbranch {state["branch"]} ではありません', f'git switch {state["branch"]} で戻ってください')
        round_no = self.next_round(state)
        if round_no > state['max_rounds']:
            raise contract('round上限に達しています', 'status で引継ぎの選択肢を確認してください')
        diff = self.drift_against_worktree()
        if crit.has_drift(diff):
            raise contract('基準ドリフト（HOLD）: 固定した受入基準が変更されています', '意図した変更なら利用者の明示指示で refreeze を実行してください', {'drift': diff})
        result = gitops.commit_round(self.root, self.change_id, round_no, self.review_rel)
        record = {'round': round_no, 'sha': result['sha'], 'committed_at': now_jst(), 'attempts': [],
                  'gate': None, 'stop': None, 'review': None, 'retry_allowed': False}
        new_state = {**state, 'rounds': [*state['rounds'], record]}
        self.write_json('state.json', new_state)
        return {'round': round_no, 'sha': result['sha'], 'paths': result['paths']}

    # --- refreeze ---
    def refreeze(self, reason: str) -> dict:
        if not reason.strip():
            raise contract('refreezeには利用者の指示内容（--reason）が必要です')
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
        state = self.state()
        return {'state': state, 'next': next_action(state, self.change_id)}


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
    n = last['round'] + 1
    return f'Findingに対応し、{state_review_rel(change_id)}/r{n}_report.md を書いてstageし、{cli} commit-round {change_id} を実行してください'


def state_review_rel(change_id: str) -> str:
    return f'openspec/changes/{change_id}/review'
