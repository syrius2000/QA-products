#!/usr/bin/env python3
"""pr-openspec: Reviewer回答の決定的な検証（標準ライブラリのみ）。

使い方: validate_review_reply.py --manifest <manifest.json> --reply <回答.md|回答.json>
出力はJSON。終了コード: 0=PASS, 1=FAIL, 2=INCONCLUSIVE, 3=使用法・入力ファイルの誤り。

判定規則は計画書（openspec/changes/add-pr-openspec-skill/design.md）の
「回答JSONのスキーマ」「全要求台帳と必須の決め方」「checkerの入出力と判定」に従う。
GitHubの現在状態は取得しない。期待値は呼び出し側がmanifestとして渡す。
checkerのPASSは、台帳に対する回答の形式と網羅性の検証に限られ、指摘の真偽は保証しない。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VERDICTS = ('conforms', 'nonconforming', 'unverified', 'out_of_scope')
IDENTITY = ('request_id', 'pr_url', 'base_sha', 'head_sha', 'request_blob_sha')
SHA40 = re.compile(r'^[0-9a-f]{40}$')
JSON_BLOCK = re.compile(r'^```json[ \t]*\n(.*?)\n```[ \t]*$', re.M | re.S)
EXIT = {'PASS': 0, 'FAIL': 1, 'INCONCLUSIVE': 2}


def extract_reply(path: Path) -> tuple[object | None, list[str]]:
    """回答ファイルから回答JSONを取り出す。.jsonはそのまま読み、それ以外はMarkdownの```json blockを正確に1つ読む。"""
    text = path.read_text(encoding='utf-8')
    if path.suffix.lower() == '.json':
        try:
            return json.loads(text), []
        except json.JSONDecodeError as exc:
            return None, [f'回答JSONの構文が不正: {exc}']
    blocks = JSON_BLOCK.findall(text)
    if len(blocks) != 1:
        return None, [f'回答Markdownの```json blockが{len(blocks)}個あります（1個だけ必要）']
    try:
        return json.loads(blocks[0]), []
    except json.JSONDecodeError as exc:
        return None, [f'JSON blockの構文が不正: {exc}']


def check_manifest(manifest: object) -> list[str]:
    """期待値manifestの妥当性。台帳が空、承認のない除外、重複IDはここで不備にする。"""
    if not isinstance(manifest, dict):
        return ['manifestがJSONオブジェクトではありません']
    problems: list[str] = []
    for key in IDENTITY:
        if not isinstance(manifest.get(key), str) or not manifest.get(key):
            problems.append(f'manifestに{key}がありません')
    for key in ('base_sha', 'head_sha'):
        value = manifest.get(key)
        if isinstance(value, str) and value and not SHA40.match(value):
            problems.append(f'manifestの{key}が完全SHA（40桁の16進）ではありません')
    ledger = manifest.get('ledger')
    if not isinstance(ledger, list) or not ledger:
        return problems + ['manifestのledger（全要求台帳）が空、または存在しません']
    seen: set[str] = set()
    for item in ledger:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str):
            problems.append('台帳の項目にidがありません')
            continue
        item_id = item['id']
        if item_id in seen:
            problems.append(f'台帳のIDが重複: {item_id}')
        seen.add(item_id)
        if not isinstance(item.get('required'), bool):
            problems.append(f'台帳 {item_id} のrequiredが真偽値ではありません')
            continue
        if item['required'] is False:
            exclusion = item.get('exclusion')
            if not (isinstance(exclusion, dict)
                    and str(exclusion.get('approved_by', '')).strip()
                    and str(exclusion.get('reason', '')).strip()):
                problems.append(f'台帳 {item_id} は除外されていますが、承認者と理由がありません')
    return problems


def _result(problems: list[str], counts: dict, kept: list[dict]) -> dict:
    """構造に不備があればINCONCLUSIVE。不備がなければ FAIL > INCONCLUSIVE > PASS の順で決める。"""
    if problems:
        result, structure = 'INCONCLUSIVE', 'invalid'
    elif counts.get('nonconforming'):
        result, structure = 'FAIL', 'valid'
    elif counts.get('unverified'):
        result, structure = 'INCONCLUSIVE', 'valid'
    else:
        result, structure = 'PASS', 'valid'
    return {'result': result, 'structure': structure, 'problems': problems,
            'counts': counts, 'kept_findings': kept}


def check_reply(manifest: dict, reply: object) -> dict:
    """回答JSONを台帳と照合する。不備は問題一覧に積み、確実なnonconformingはkept_findingsに残す。"""
    if not isinstance(reply, dict):
        return _result(['回答JSONがオブジェクトではありません'], {}, [])
    problems: list[str] = []
    kept: list[dict] = []
    counts = {verdict: 0 for verdict in VERDICTS}

    if reply.get('schema_version') != 1:
        problems.append('schema_versionが1ではありません')
    for key in IDENTITY:
        if key not in reply:
            problems.append(f'回答に{key}がありません')
        elif reply[key] != manifest.get(key):
            problems.append(f'{key}が期待値と一致しません（回答: {reply[key]!r}、期待: {manifest.get(key)!r}）')

    reviewer = reply.get('reviewer')
    if not isinstance(reviewer, dict):
        problems.append('reviewer（tool・model・version）がありません')
    else:
        for key in ('tool', 'model', 'version'):
            if not isinstance(reviewer.get(key), str) or not reviewer[key].strip():
                problems.append(f'reviewer.{key}がありません')

    criteria = reply.get('criteria')
    findings = reply.get('findings', [])
    if not isinstance(criteria, list):
        problems.append('criteriaが配列ではありません')
        criteria = []
    if not isinstance(findings, list):
        problems.append('findingsが配列ではありません')
        findings = []
    if not isinstance(reply.get('unverified_items', []), list):
        problems.append('unverified_itemsが配列ではありません')

    ledger = {item['id']: item for item in manifest.get('ledger', [])
              if isinstance(item, dict) and isinstance(item.get('id'), str)}
    ids: list[str] = []
    for criterion in criteria:
        if not isinstance(criterion, dict) or not isinstance(criterion.get('id'), str):
            problems.append('criteriaの項目にidがありません')
            continue
        cid = criterion['id']
        ids.append(cid)
        verdict = criterion.get('verdict')
        if verdict not in VERDICTS:
            problems.append(f'{cid}: verdictが許容外（{verdict!r}）')
            continue
        counts[verdict] += 1
        evidence = criterion.get('evidence', [])
        has_evidence = isinstance(evidence, list) and any(str(e).strip() for e in evidence)
        reason = str(criterion.get('reason') or '').strip()
        if verdict in ('conforms', 'nonconforming') and not has_evidence:
            problems.append(f'{cid}: {verdict}には根拠（evidence）が1件以上必要')
        if verdict in ('nonconforming', 'unverified', 'out_of_scope') and not reason:
            problems.append(f'{cid}: {verdict}には理由（reason）が必要')
        if verdict == 'nonconforming':
            kept.append({'criterion_id': cid, 'verdict': 'nonconforming'})
        if verdict == 'out_of_scope':
            item = ledger.get(cid)
            if item is None or item.get('required') is not False or not item.get('exclusion'):
                problems.append(f'{cid}: out_of_scopeは承認済みの除外（required: false、exclusionあり）の基準にだけ使えます')

    for cid in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f'基準IDが重複: {cid}')
    for cid in sorted(set(ledger) - set(ids)):
        problems.append(f'台帳の基準が回答にありません: {cid}')
    for cid in sorted(set(ids) - set(ledger)):
        problems.append(f'台帳にない基準IDです: {cid}')
    for finding in findings:
        target = finding.get('criterion_id') if isinstance(finding, dict) else None
        if target not in set(ids):
            problems.append(f'findingsのcriterion_idが回答のcriteriaにありません: {target!r}')

    return _result(problems, counts, kept)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='pr-openspec: Reviewer回答を期待値manifestと照合する')
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--reply', required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({'result': 'USAGE', 'error': f'manifestを読めません: {exc}'}, ensure_ascii=False))
        return 3
    if not args.reply.is_file():
        print(json.dumps({'result': 'USAGE', 'error': f'回答ファイルがありません: {args.reply}'}, ensure_ascii=False))
        return 3

    problems = check_manifest(manifest)
    reply, reply_problems = (None, [])
    if not problems:
        reply, reply_problems = extract_reply(args.reply)
    if problems or reply_problems:
        out = _result(problems + reply_problems, {}, [])
    else:
        out = check_reply(manifest, reply)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return EXIT[out['result']]


if __name__ == '__main__':
    sys.exit(main())
