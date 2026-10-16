"""reviewサブコマンド。round SHAの一時worktreeで必須checkとReviewerを実行し、Gateを判定する。"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from . import criteria as crit
from . import gate, gitops, report, reviewers, schema
from .errors import contract
from .session import Session, now_jst

MAX_ATTEMPTS = 2  # 初回 + 再試行1回
CONTRACT_PATH = Path(__file__).resolve().parents[2] / 'references' / 'reviewer_contract.md'


def run_checks(checks: list[dict], worktree: Path) -> list[dict]:
    results = []
    for check in checks:
        base = {'id': check['id'], 'exit_code': None}
        try:
            proc = subprocess.run(check['argv'], cwd=worktree / check['cwd'], capture_output=True, text=True,
                                  timeout=check['timeout'], env=reviewers.quiet_env())
        except FileNotFoundError:
            results.append({**base, 'status': 'ERROR', 'reason': f'{check["argv"][0]} が見つかりません'})
            continue
        except subprocess.TimeoutExpired:
            results.append({**base, 'status': 'ERROR', 'reason': f'timeout（{check["timeout"]}秒）'})
            continue
        except OSError as exc:
            results.append({**base, 'status': 'ERROR', 'reason': f'実行できません: {exc}'})
            continue
        tail = (proc.stdout + proc.stderr).strip()[-300:]
        ok = proc.returncode == check['expected_exit']
        results.append({'id': check['id'], 'exit_code': proc.returncode, 'status': 'PASS' if ok else 'FAIL',
                        'reason': f'期待 {check["expected_exit"]}・実際 {proc.returncode}' + (f': {tail}' if tail and not ok else '')})
    return results


def build_prompt(session: Session, state: dict, record: dict, frozen: dict, checks: list[dict],
                 previous_open: list[dict], tool: str) -> str:
    base, sha = state['base_sha'], record['sha']
    report_path = session.path(f'r{record["round"]}_report.md')
    stat = gitops.git(session.root, 'diff', '--stat', f'{base}..{sha}')
    payload = {
        'change_id': session.change_id, 'round': record['round'], 'base_sha': base, 'round_sha': sha,
        'criteria_fingerprint': frozen['fingerprint'], 'reviewer.tool': tool,
    }
    sections = [
        CONTRACT_PATH.read_text(encoding='utf-8'),
        '---', '# 今回のレビュー', '```json', json.dumps(payload, ensure_ascii=False, indent=2), '```',
        f'範囲外かどうかの判断には `{session.change_rel}/proposal.md` のWhyと対象外を参照する。',
        '## 受入基準（この順序・原文のまま criteria に並べる）', '```json',
        json.dumps([{'id': c['id'], 'text': c['text']} for c in frozen['criteria']], ensure_ascii=False, indent=2), '```',
        '## 必須checkの結果（CLIがround SHAで実行済み）', '```json', json.dumps(checks, ensure_ascii=False, indent=2), '```',
        f'## 変更の概要（git diff --stat {base[:12]}..{sha[:12]}）', '```', stat.strip() or '（差分なし）', '```',
        f'## 実装報告（r{record["round"]}_report.md、実装担当の自己申告）', report_path.read_text(encoding='utf-8'),
        '## 前roundの未解決Finding（全IDを同じIDで再判定する）', '```json',
        json.dumps(previous_open, ensure_ascii=False, indent=2) if previous_open else '[]', '```',
        '## 出力スキーマ（checksはCLIが置き換える）', '```json', schema.SCHEMA_PATH.read_text(encoding='utf-8'), '```',
    ]
    return '\n'.join(sections)


def review(session: Session, reviewer: str | None = None, model: str | None = None, timeout: int | None = None,
           effort: str | None = None) -> dict:
    state = session.state()
    if state['status'] != 'active' or not state['rounds']:
        raise contract('レビューできるroundがありません', 'status で次の操作を確認してください')
    record = state['rounds'][-1]
    if record.get('gate') is not None and not record.get('retry_allowed'):
        raise contract(f'r{record["round"]}はレビュー済みです', 'status で次の操作を確認してください')
    tool = reviewer or state['reviewer']
    model = model or state.get('model')
    effort = effort or state.get('effort')
    if effort and not re.fullmatch(r'[a-z]+', effort):
        raise contract('effortは英小文字で指定してください（例: low／medium／high）')
    probe = reviewers.probe(tool)
    if not probe['ok']:
        raise contract(f'Reviewer {tool} を使えません: {probe.get("problem")}',
                       f'導入する（{probe["install"]}）か、--reviewer で別のReviewerを選んでください。doctor で確認できます', {'doctor': probe})
    frozen = session.frozen()
    prev_review = next((r['review'] for r in reversed(state['rounds'][:-1]) if r.get('review')), None)
    previous_open = [f for f in (prev_review or {}).get('findings', []) if f['status'] in gate.OPEN_STATUSES]
    attempt = {'at': now_jst(), 'tool': tool, 'version': probe['version']}
    with gitops.review_worktree(session.root, record['sha']) as wt:
        diff = crit.drift(frozen, crit.build(wt, session.change_id, allow_empty=True))
        if crit.has_drift(diff):
            return _finish_round(session, state, record, attempt, None, [], diff=diff, previous=prev_review, probe=probe)
    # checkは専用のworktreeで実行する。checkが追跡ファイルを変えても、Reviewerは改変のないround SHAを読む
    with gitops.review_worktree(session.root, record['sha']) as check_wt:
        checks = run_checks(frozen['checks'], check_wt)
    with gitops.review_worktree(session.root, record['sha']) as wt:
        before_main = gitops.status_entries(session.root)
        prompt = build_prompt(session, state, record, frozen, checks, previous_open, tool)
        result = reviewers.run(tool, prompt, wt, timeout or state['timeout'], model, probe, effort)
        wrote = gitops.status_entries(wt)  # 新しいworktreeなので、どの変更もReviewerの書込み
        changed_main = sorted(set(gitops.status_entries(session.root)) ^ set(before_main))
    attempt['model'] = result['model']
    if not result['ok']:
        return _finish_round(session, state, record, {**attempt, 'error': result['error']}, None, [result['error']],
                             raw=result.get('raw'), previous=prev_review, probe=probe)
    if wrote or changed_main:
        paths = [f'{xy} {p}' for xy, p in [*wrote, *changed_main]][:20]
        error = f'Reviewerが作業ツリーへ書き込みました（読取り専用契約違反）: {", ".join(paths)}'
        return _finish_round(session, state, record, {**attempt, 'error': error}, None, [error], raw=result.get('raw'), previous=prev_review, probe=probe)
    data = {**result['data'], 'checks': checks}
    schema_errors = schema.validate(data)  # 格下げ処理の前に型を保証する
    if schema_errors:
        return _finish_round(session, state, record, {**attempt, 'error': 'スキーマ不適合'}, None, schema_errors, raw=result.get('raw'), previous=prev_review, probe=probe)
    data = gate.demote_proposals(data, frozen, keep_ids=tuple(f['id'] for f in previous_open))
    errors, provenance = gate.structural_errors(data, frozen, base_sha=state['base_sha'], round_sha=record['sha'],
                                                round_no=record['round'], previous_open=[f['id'] for f in previous_open])
    if errors:
        return _finish_round(session, state, record, {**attempt, 'error': 'スキーマ不適合'}, None, errors, raw=result.get('raw'), previous=prev_review, probe=probe)
    return _finish_round(session, state, record, attempt, data, [], provenance=provenance, previous=prev_review, probe=probe)


def _finish_round(session: Session, state: dict, record: dict, attempt: dict, review_data: dict | None, errors: list[str], *,
                  diff: dict | None = None, provenance: list[str] | None = None, raw: str | None = None,
                  previous: dict | None = None, probe: dict) -> dict:
    attempts = [*record['attempts'], attempt]
    drifted = bool(diff and crit.has_drift(diff))
    failed = review_data is None and not drifted
    retryable = (failed or bool(provenance)) and len(attempts) < MAX_ATTEMPTS
    verdict = gate.decide(review_data if not failed else None, provenance=provenance, drift=drifted)
    if drifted:
        verdict['reasons'].append(f'変更された基準: {json.dumps(diff, ensure_ascii=False)}')
    stop = ({'stop': False, 'reason': 'retry', 'stalled': []} if retryable
            else gate.stop_decision(verdict['gate'], record['round'], state['max_rounds'], review_data, previous))
    reviewer_info = {'tool': attempt['tool'], 'version': attempt.get('version') or probe.get('version') or 'unknown',
                     'model': attempt.get('model', 'unknown')}
    new_record = {**record, 'attempts': attempts, 'gate': verdict, 'stop': stop, 'review': review_data,
                  'retry_allowed': retryable, 'reviewer': reviewer_info, 'structural_errors': errors, 'reviewed_at': now_jst()}
    rounds = [*state['rounds'][:-1], new_record]
    new_state = {**state, 'rounds': rounds}
    if stop['stop']:
        new_state = {**new_state, 'status': 'stopped', 'stop_reason': stop['reason']}
    name = f'r{record["round"]}_review'
    full = {**new_record, 'change_id': session.change_id, 'base_sha': state['base_sha']}
    session.write_json(f'{name}.json', full)
    session.write_text(f'{name}.md', report.review_markdown(full))
    if raw is not None:
        session.write_text(f'{name}.attempt{len(attempts)}.raw.txt', raw)
    session.write_json('state.json', new_state)
    return {'record': full, 'state': new_state, 'reviewer_failed': failed}
