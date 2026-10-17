"""人向けのテキスト表示。"""
from __future__ import annotations

from .report import STOP_JA
from .session import next_action

HANDOFF = '選択肢: 人の判断 ／ quality-review の review-standalone ／ blind-qa-cycle'


def render_text(op: str, result: dict, change_id: str | None) -> str:
    if result.get('status') == 'error':
        lines = [f'停止: {result["message"]}']
        if result.get('action'):
            lines.append(f'次の操作: {result["action"]}')
        for key, value in result.get('details', {}).items():
            items = value if isinstance(value, list) else [value]
            lines += [f'  {key}: {item}' for item in items]
        return '\n'.join(lines)
    return {'start': _start, 'commit-round': _commit, 'review': _review, 'status': _status,
            'finish': _finish, 'prune': _prune, 'refreeze': _refreeze, 'doctor': _doctor}[op](result)


def _start(r: dict) -> str:
    doc, state = r['criteria'], r['state']
    c = doc['counts']
    lines = [f'開始しました: {state["change_id"]}（branch {state["branch"]}、base {state["base_sha"][:12]}）',
             f'受入基準: タスク {c["tasks"]}件、Scenario {c["scenarios"]}件、必須check {c["checks"]}件']
    if c['ignored_unnumbered_tasks']:
        lines.append(f'注意: 番号なしタスク {c["ignored_unnumbered_tasks"]}件は基準に含めていません')
    lines += [f'  {item["id"]}: {_headline(item)}' for item in doc['criteria']]
    lines += [f'  {chk["id"]}: {" ".join(chk["argv"])}' for chk in doc['checks']]
    probe = r['reviewer_probe']
    lines.append(f'Reviewer: {probe["tool"]} {probe.get("version") or ""} ' + ('（利用可）' if probe['ok'] else f'（利用不可: {probe.get("problem")}）'))
    if r['pending_change_files']:
        lines.append('change配下の未commit変更（round 1でcommitする場合はstageしてください）:')
        lines += [f'  {p}' for p in r['pending_change_files']]
    lines.append('次の操作: ' + next_action(state, state['change_id']))
    return '\n'.join(lines)


def _headline(item: dict) -> str:
    lines = item['text'].splitlines()
    return (lines[1] if item['kind'] == 'scenario' and len(lines) > 1 else lines[0])[:80]


def _commit(r: dict) -> str:
    return '\n'.join([f'r{r["round"]} をcommitしました: {r["sha"][:12]}', *[f'  {p}' for p in r['paths']],
                      '次の操作: review を実行してください'])


def _review(r: dict) -> str:
    rec, state = r['record'], r['state']
    lines = [f'r{rec["round"]} Gate: {rec["gate"]["gate"]}（{"; ".join(rec["gate"]["reasons"])}）',
             f'Reviewer: {rec["reviewer"]["tool"]} {rec["reviewer"]["version"]} ／ model {rec["reviewer"]["model"]}']
    lines += [f'構造不適合: {e}' for e in rec.get('structural_errors', [])]
    if rec.get('retry_allowed'):
        lines.append('このroundは1回だけ再試行できます（review を再実行）')
    review = rec.get('review') or {}
    for f in review.get('findings', []):
        lines.append(f'  {f["id"]} [{f["status"]}/{f["severity"]}] {f["location"]}: {f["description"]}')
    for p in review.get('proposals', []):
        lines.append(f'  提案 {p["id"]}: {p["description"]}')
    stop = rec['stop']
    if stop['stop']:
        lines.append(f'停止: {STOP_JA.get(stop["reason"], stop["reason"])}' + (f'（{", ".join(stop["stalled"])}）' if stop['stalled'] else ''))
        if stop['reason'] in ('stagnation', 'max-rounds'):
            lines.append(HANDOFF)
    lines.append('次の操作: ' + next_action(state, state['change_id']))
    return '\n'.join(lines)


def _status(r: dict) -> str:
    s = r['state']
    lines = [f'{s["change_id"]}: {s["status"]}（branch {s["branch"]}、base {s["base_sha"][:12]}、上限 {s["max_rounds"]} round、Reviewer {s["reviewer"]}）']
    for rec in s['rounds']:
        g = rec['gate']['gate'] if rec.get('gate') else '未レビュー'
        lines.append(f'  r{rec["round"]} {rec["sha"][:12]} Gate {g}')
    if s['status'] == 'stopped' and s.get('stop_reason') in ('stagnation', 'max-rounds'):
        lines.append(HANDOFF)
    lines.append('次の操作: ' + r['next'])
    return '\n'.join(lines)


def _finish(r: dict) -> str:
    head = 'squash計画（dry-run。実行するには --confirm）' if r['dry_run'] else f'squashしました: {r["squashed_sha"][:12]}（tree一致を確認済み）'
    lines = [head, f'base: {r["base_sha"][:12]} ／ Gate: {r["gate"]}', 'まとめるcommit:', *[f'  {c}' for c in r['commits']]]
    if r['dry_run'] and r['pending_review_files']:
        lines += ['summary commitに含めるreview成果物:', *[f'  {p}' for p in r['pending_review_files']]]
    lines += [f'バックアップref: {r["backup_ref"]}', 'commit message:', *[f'  {line}' for line in r['message'].splitlines()]]
    if not r['dry_run']:
        lines.append('openspec archive の実行は利用者が判断してください（自動実行しません）')
    return '\n'.join(lines)


def _prune(r: dict) -> str:
    lines = ['削除対象のバックアップref:', *[f'  {x["ref"]} {x["sha"][:12]}' for x in r['refs']],
             '削除後に到達できなくなるSHA:', *([f'  {sha}' for sha in r['unreachable_after_prune']] or ['  なし'])]
    lines.append('確認のうえ --confirm で削除してください' if r['dry_run'] else f'削除しました: {len(r["deleted"])}件')
    return '\n'.join(lines)


def _refreeze(r: dict) -> str:
    d = r['drift']
    return '\n'.join([f'受入基準を再固定しました（追加 {d["added"]}、削除 {d["removed"]}、変更 {d["changed"]}）',
                      'HOLDを解除しました。次のroundをcommitしてください' if r['reopened'] else ''])


def _doctor(r: dict) -> str:
    lines = [f'{name}: {t["version"] or "未導入"}' for name, t in r['tools'].items()]
    for name, p in r['reviewers'].items():
        mark = '利用可' if p['ok'] else f'利用不可（{p.get("problem")}）。導入: {p["install"]}'
        lines.append(f'Reviewer {name}: {p.get("version") or "-"} {mark}')
    lines.append(f'選択中のReviewer {r["selected"]}: ' + ('OK' if r['ok'] else '利用できません。導入するか --reviewer で切り替えてください'))
    return '\n'.join(lines)
