"""レビューJSONと状態から人向けMarkdownを生成する。"""
from __future__ import annotations

from .gate import latest_review

STATUS_JA = {'new': '新規', 'resolved': '解消', 'unresolved': '未解消', 'unverified': '未検証', 'withdraw-proposed': '撤回提案'}
STOP_JA = {'pass': 'PASS', 'hold': 'HOLD（中断）', 'stagnation': 'Findingの停滞', 'max-rounds': 'round上限', 'continue': '継続'}


def _cell(text) -> str:
    return str(text).replace('|', '\\|').replace('\n', '<br>')


def review_markdown(record: dict) -> str:
    """r<N>_review.md。recordはround記録（gate・review・attemptsを含む）。"""
    review = record.get('review')
    lines = [f'# spec-review r{record["round"]}: {record["change_id"]}', '',
             f'- Gate: **{record["gate"]["gate"]}**（{"; ".join(record["gate"]["reasons"])}）',
             f'- base SHA: `{record["base_sha"]}`', f'- round SHA: `{record["sha"]}`',
             f'- Reviewer: {record["reviewer"]["tool"]} {record["reviewer"]["version"]} ／ model: {record["reviewer"]["model"]}',
             f'- 停止判定: {STOP_JA.get(record["stop"]["reason"], record["stop"]["reason"])}', '']
    if record.get('structural_errors'):
        lines += ['## 構造不適合', ''] + [f'- {e}' for e in record['structural_errors']] + ['']
    if not review:
        lines += ['有効なレビュー結果はありません。', '']
        return '\n'.join(lines)
    lines += ['## 受入基準', '', '| ID | 判定 | 根拠 |', '|---|---|---|']
    lines += [f'| {c["id"]} | {c["verdict"]} | {_cell(c["evidence"])} |' for c in review['criteria']]
    lines += ['', '## 必須check', '', '| ID | 状態 | 終了code | 理由 |', '|---|---|---|---|']
    lines += [f'| {c["id"]} | {c["status"]} | {c["exit_code"]} | {_cell(c["reason"])} |' for c in review['checks']]
    lines += ['', '## Finding', '']
    if review['findings']:
        lines += ['| ID | 状態 | 重大度 | 種別 | 基準 | 場所 | 内容 | 対応案 |', '|---|---|---|---|---|---|---|---|']
        lines += [f'| {f["id"]} | {STATUS_JA[f["status"]]} | {f["severity"]} | {f["kind"]} | {", ".join(f["criterion_ids"])} | '
                  f'{_cell(f["location"])} | {_cell(f["description"])} | {_cell(f["recommendation"])} |' for f in review['findings']]
    else:
        lines.append('なし')
    lines += ['', '## 提案（Gate・停滞判定の対象外）', '']
    lines += [f'- {p["id"]}: {p["description"]}（{p["rationale"]}）' for p in review['proposals']] or ['なし']
    lines += ['', '## 所見', '', review.get('summary') or '（なし）', '']
    return '\n'.join(lines)


def summary_markdown(state: dict, finish: dict) -> str:
    """summary.md。round推移とsquash前SHAを残す。"""
    rounds = state['rounds']
    last = rounds[-1]
    lines = [f'# spec-review summary: {state["change_id"]}', '',
             f'- branch: `{state["branch"]}`', f'- base SHA: `{state["base_sha"]}`',
             f'- round数: {len(rounds)}（上限 {state["max_rounds"]}）',
             f'- 最終Gate: **{last["gate"]["gate"]}**',
             f'- squash前の最終SHA: `{finish["pre_squash_sha"]}`',
             f'- バックアップref: `{finish["backup_ref"]}`（`prune`で削除するとround SHAへ到達できなくなる）', '']
    if finish.get('accept_residual'):
        lines += [f'- 残余の受容（利用者）: {finish["accept_residual"]}', '']
    lines += ['## Gate推移', '', '| round | SHA | Gate | 停止判定 | Reviewer | model | 未解決Finding |', '|---|---|---|---|---|---|---|']
    for r in rounds:
        review = r.get('review') or {}
        open_ids = [f['id'] for f in review.get('findings', []) if f['status'] in ('new', 'unresolved', 'unverified')]
        lines.append(f'| r{r["round"]} | `{r["sha"]}` | {r["gate"]["gate"]} | {STOP_JA.get(r["stop"]["reason"], r["stop"]["reason"])} | '
                     f'{r["reviewer"]["tool"]} {r["reviewer"]["version"]} | {r["reviewer"]["model"]} | {", ".join(open_ids) or "なし"} |')
    source_round, review = latest_review(rounds)
    review = review or {}
    heading = '最終round' if source_round == last['round'] else f'有効なレビューがある最新round r{source_round}'
    lines += ['', f'## 受入基準（{heading}）', '']
    if source_round is not None and source_round != last['round']:
        lines += [f'最終round r{last["round"]}には有効なレビュー結果がないため、r{source_round}の判定と未解決Findingを引き継ぐ。', '']
    if review.get('criteria'):
        lines += ['| ID | 判定 |', '|---|---|'] + [f'| {c["id"]} | {c["verdict"]} |' for c in review['criteria']]
        lines += [f'| {c["id"]} | {c["status"]} |' for c in review.get('checks', [])]
    else:
        lines.append('有効なレビュー結果がありません')
    residual = [f for f in review.get('findings', []) if f['status'] in ('new', 'unresolved', 'unverified')]
    lines += ['', '## 残余Finding', '']
    lines += [f'- {f["id"]}（{STATUS_JA[f["status"]]}・{f["severity"]}）: {f["description"]}' for f in residual] or ['なし']
    proposals = review.get('proposals', [])
    lines += ['', '## 残った提案', '']
    lines += [f'- {p["id"]}: {p["description"]}' for p in proposals] or ['なし']
    lines.append('')
    return '\n'.join(lines)
