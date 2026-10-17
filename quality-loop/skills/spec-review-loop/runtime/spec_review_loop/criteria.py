"""OpenSpec changeから受入基準を抽出し、要件指紋で固定する。

基準の原文は元の行をそのまま使う（空白も含む）。タスクはチェックボックス記号だけを除き、
ブロック末尾の空行は区切りとして除く。指紋はこの原文のUTF-8 bytesのSHA-256である。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .errors import contract

TASK_RE = re.compile(r'^\s*- \[([ xX])\] (\d+(?:\.\d+)+)\.?\s+(.*)$')
UNNUMBERED_TASK_RE = re.compile(r'^\s*- \[[ xX]\] ')
SECTION_RE = re.compile(r'^## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements\s*$')
REQUIREMENT_RE = re.compile(r'^### Requirement:\s*(.+?)\s*$')
SCENARIO_RE = re.compile(r'^#### Scenario:\s*(.+?)\s*$')
VERIFY_RE = re.compile(r'検証[:：]')
CHECK_ID_RE = re.compile(r'^CHK-[A-Z0-9_-]+$')
DEFAULT_CHECK_TIMEOUT = 300


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def change_dir(root: Path, change_id: str) -> Path:
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', change_id):
        raise contract(f'change IDの形式が不正です: {change_id}', 'openspec list で正しいIDを確認してください')
    path = root / 'openspec' / 'changes' / change_id
    if not path.is_dir():
        raise contract(f'OpenSpec changeが見つかりません: openspec/changes/{change_id}', 'openspec list で対象changeを確認してください')
    return path


def extract_tasks(tasks_md: Path) -> tuple[list[dict], int]:
    """番号付きタスクと、無視した番号なしタスクの件数を返す。"""
    if not tasks_md.is_file():
        return [], 0
    tasks: list[dict] = []
    ignored = 0
    current: dict | None = None
    for lineno, line in enumerate(tasks_md.read_text(encoding='utf-8').splitlines(), 1):
        match = TASK_RE.match(line)
        if match:
            current = {'number': match.group(2), 'lines': [line[match.start(2):]], 'line': lineno}
            tasks.append(current)
            continue
        if UNNUMBERED_TASK_RE.match(line):
            ignored += 1
            current = None
            continue
        if current is not None and line.strip() and line[:1].isspace() and not line.lstrip().startswith('#'):
            current['lines'].append(line)
            continue
        if not line.strip() or line.startswith('#'):
            current = None
    result = []
    seen = set()
    for task in tasks:
        cid = f'T-{task["number"]}'
        if cid in seen:
            raise contract(f'tasks.mdのタスク番号が重複しています: {task["number"]}', 'タスク番号を一意にしてから再実行してください')
        seen.add(cid)
        text = '\n'.join(task['lines'])
        parts = VERIFY_RE.split(text, maxsplit=1)
        result.append({
            'id': cid, 'kind': 'task', 'source': f'tasks.md:{task["line"]}', 'text': text,
            'verification': parts[1].strip() if len(parts) == 2 else '',
        })
    return result, ignored


def _capability(specs_root: Path, spec_md: Path) -> str:
    return '/'.join(spec_md.parent.relative_to(specs_root).parts)


def extract_scenarios(specs_root: Path) -> list[dict]:
    if not specs_root.is_dir():
        return []
    result: list[dict] = []
    for spec_md in sorted(specs_root.rglob('spec.md')):
        cap = _capability(specs_root, spec_md)
        rel = spec_md.relative_to(specs_root.parent).as_posix()
        result.extend(_scenarios_in(spec_md, cap, rel))
    return result


def _scenarios_in(spec_md: Path, cap: str, rel: str) -> list[dict]:
    lines = spec_md.read_text(encoding='utf-8').splitlines()
    has_delta = any(SECTION_RE.match(line) for line in lines)
    op = None if has_delta else 'ADDED'
    requirements: list[dict] = []
    req = None
    scenario = None
    for lineno, line in enumerate(lines, 1):
        section = SECTION_RE.match(line)
        if section or (line.startswith('## ') and not line.startswith('### ')):
            op = section.group(1) if section else (None if has_delta else 'ADDED')
            req = scenario = None
            continue
        if op not in ('ADDED', 'MODIFIED', 'REMOVED'):
            continue
        heading = REQUIREMENT_RE.match(line)
        if heading:
            req = {'name': heading.group(1), 'raw': line, 'op': op, 'body': [], 'scenarios': [], 'line': lineno}
            requirements.append(req)
            scenario = None
            continue
        if req is None:
            continue
        title = SCENARIO_RE.match(line)
        if title:
            scenario = {'title': title.group(1), 'raw': line, 'lines': [], 'line': lineno}
            req['scenarios'].append(scenario)
            continue
        if line.startswith('#'):
            scenario = None
            continue
        target = scenario['lines'] if scenario is not None else req['body']
        target.append(line)
    result = []
    for k, req in enumerate(requirements, 1):
        header = f'{req["op"]}: {req["raw"]}'
        if not req['scenarios']:
            if req['op'] != 'REMOVED':
                continue
            result.append({'id': f'S-{cap}-{k}.0', 'kind': 'removed', 'source': f'{rel}:{req["line"]}',
                           'text': _block([header, *req['body']]), 'operation': req['op']})
            continue
        for n, sc in enumerate(req['scenarios'], 1):
            result.append({'id': f'S-{cap}-{k}.{n}', 'kind': 'scenario', 'source': f'{rel}:{sc["line"]}',
                           'text': _block([header, sc['raw'], *sc['lines']]), 'operation': req['op']})
    return result


def _block(lines: list[str]) -> str:
    """原文の行をそのまま連結する。先頭以外の前後の空行（区切り）だけを除く。"""
    head, body = lines[0], list(lines[1:])
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    return '\n'.join([head, *body])


def load_checks(review_dir: Path, change_id: str) -> list[dict]:
    checks = [{'id': 'CHK-VALIDATE', 'argv': ['openspec', 'validate', '--strict', change_id],
               'cwd': '.', 'timeout': DEFAULT_CHECK_TIMEOUT, 'expected_exit': 0}]
    path = review_dir / 'checks.json'
    if not path.exists():
        return checks
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise contract(f'review/checks.jsonを読めません: {exc}', 'JSONの形式を修正してください') from exc
    items = data.get('checks') if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise contract('review/checks.jsonはcheckの配列、または{"checks": [...]}である必要があります')
    for item in items:
        checks.append(_validate_check(item))
    ids = [c['id'] for c in checks]
    if len(ids) != len(set(ids)):
        raise contract('check IDが重複しています（CHK-VALIDATEは予約済み）', 'check IDを一意にしてください')
    return checks


def _validate_check(item) -> dict:
    if not isinstance(item, dict):
        raise contract('checkはオブジェクトで指定してください')
    cid, argv = item.get('id'), item.get('argv')
    if not isinstance(cid, str) or not CHECK_ID_RE.match(cid):
        raise contract(f'check IDはCHK-<英大文字・数字>の形式が必要です: {cid!r}')
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) and a for a in argv):
        raise contract(f'{cid}: argvは空でない文字列の配列で指定してください（shell文字列は不可）')
    cwd = item.get('cwd', '.')
    if not isinstance(cwd, str) or cwd.startswith('/') or '..' in Path(cwd).parts:
        raise contract(f'{cid}: cwdはリポジトリ内の相対pathで指定してください')
    timeout = item.get('timeout', DEFAULT_CHECK_TIMEOUT)
    expected = item.get('expected_exit', 0)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        raise contract(f'{cid}: timeoutは正の整数（秒）で指定してください')
    if not isinstance(expected, int) or isinstance(expected, bool):
        raise contract(f'{cid}: expected_exitは整数で指定してください')
    return {'id': cid, 'argv': list(argv), 'cwd': cwd, 'timeout': timeout, 'expected_exit': expected}


def _with_fingerprints(items: list[dict], kind: str) -> list[dict]:
    out = []
    for item in items:
        basis = item['text'] if kind == 'criterion' else json.dumps(
            {k: item[k] for k in ('argv', 'cwd', 'timeout', 'expected_exit')}, ensure_ascii=False, sort_keys=True)
        out.append({**item, 'fingerprint': sha256(basis)})
    return out


def set_fingerprint(criteria: list[dict], checks: list[dict]) -> str:
    return sha256('\n'.join(f'{c["id"]}:{c["fingerprint"]}' for c in [*criteria, *checks]))


def build(root: Path, change_id: str, allow_empty: bool = False) -> dict:
    """change配下から基準を抽出する。0件なら拒否する（ドリフト検出用の再抽出ではallow_emptyで空集合を返す）。"""
    cdir = change_dir(root, change_id)
    tasks, ignored = extract_tasks(cdir / 'tasks.md')
    scenarios = extract_scenarios(cdir / 'specs')
    criteria = _with_fingerprints([*tasks, *scenarios], 'criterion')
    if not criteria and not allow_empty:
        raise contract('受入基準を抽出できません（tasks.mdの番号付きタスクもspec deltaのScenarioもありません）',
                       'tasks.mdに「- [ ] N.M …」形式のタスク、またはspecs/<cap>/spec.mdにScenarioを追加してください')
    checks = _with_fingerprints(load_checks(cdir / 'review', change_id), 'check')
    return {
        'schema_version': 1, 'change_id': change_id,
        'fingerprint': set_fingerprint(criteria, checks),
        'counts': {'tasks': len(tasks), 'scenarios': len(scenarios), 'checks': len(checks), 'ignored_unnumbered_tasks': ignored},
        'criteria': criteria, 'checks': checks,
    }


def drift(frozen: dict, current: dict) -> dict:
    """固定済みの基準と再抽出結果の差分。空のリストだけならドリフトなし。"""
    def index(doc):
        return {c['id']: c['fingerprint'] for c in [*doc['criteria'], *doc['checks']]}
    old, new = index(frozen), index(current)
    return {
        'added': [i for i in new if i not in old],
        'removed': [i for i in old if i not in new],
        'changed': [i for i in old if i in new and old[i] != new[i]],
    }


def has_drift(diff: dict) -> bool:
    return any(diff.values())
