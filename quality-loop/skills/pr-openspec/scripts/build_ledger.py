#!/usr/bin/env python3
"""pr-openspec: 監査対象HのspecデルタからR（Requirement）とS（Scenario）の全台帳を作る（標準ライブラリとgit）。

使い方: build_ledger.py --root <repo> --head <H> --change <change-id>
出力: {"head_sha": ..., "ledger": [...]} のJSON。台帳が0件なら終了コード2。使用法・git・構文の誤りは3。

対象は openspec/changes/<change-id>/specs/**/spec.md のうち、
## ADDED / MODIFIED / RENAMED / REMOVED Requirements 配下の全要求（RENAMEDはTOの名前）と、その全 #### Scenario:。
項目IDは R:<出典path>#<要求の番号> と S:<出典path>#<要求の番号>.<シナリオの番号>。
既定では全項目 required: true。除外は利用者の承認を、manifestへ手で入れた場合だけ許す（本スクリプトは除外を作らない）。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DELTA = re.compile(r'^## (ADDED|MODIFIED|RENAMED|REMOVED) Requirements\s*$')
ANY_H2 = re.compile(r'^## ')
REQ = re.compile(r'^### Requirement:\s*(.+?)\s*$')
SCN = re.compile(r'^#### Scenario:\s*(.+?)\s*$')
RENAME_FROM = re.compile(r'^-\s*FROM:\s*`?###\s*Requirement:\s*(.+?)`?\s*$')
RENAME_TO = re.compile(r'^-\s*TO:\s*`?###\s*Requirement:\s*(.+?)`?\s*$')


def git(root: Path, *args: str) -> str:
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True).stdout


def item(item_id: str, kind: str, title: str, source: str, blob: str, delta: str) -> dict:
    return {'id': item_id, 'kind': kind, 'title': title, 'source': source,
            'blob_sha': blob, 'delta': delta, 'required': True, 'exclusion': None}


def parse(text: str, source: str, blob: str) -> list[dict]:
    """specデルタを読み、R（要求）とS（シナリオ）の項目を、出現順に返す。

    ADDED・MODIFIED・REMOVEDは「### Requirement:」の見出しを読む。
    RENAMEDは「- FROM: ### Requirement: 旧名」と「- TO: ### Requirement: 新名」の対で読み、TOの名前を要求の項目にする。
    FROMの対応するTOがないまま、区切りや終わりに達した場合は構文の誤りとする。
    """
    items: list[dict] = []
    delta: str | None = None
    req_no = 0
    scn_no = 0
    current_req = False
    pending_from: str | None = None
    for line in text.splitlines():
        section = DELTA.match(line)
        if section or ANY_H2.match(line):
            if pending_from is not None:
                raise ValueError(f'{source}: FROM「{pending_from}」に対応するTOがありません')
            delta = section.group(1) if section else None
            current_req = False
            continue
        if delta is None:
            continue
        if delta == 'RENAMED':
            frm = RENAME_FROM.match(line)
            if frm:
                if pending_from is not None:
                    raise ValueError(f'{source}: FROM「{pending_from}」に対応するTOがありません')
                pending_from = frm.group(1)
                continue
            to = RENAME_TO.match(line)
            if to:
                if pending_from is None:
                    raise ValueError(f'{source}: FROMのないTOがあります: {to.group(1)}')
                req_no += 1
                scn_no = 0
                current_req = True
                items.append(item(f'R:{source}#{req_no}', 'requirement',
                                  f'{to.group(1)}（旧名: {pending_from}）', source, blob, delta))
                pending_from = None
                continue
        req = REQ.match(line)
        if req:
            req_no += 1
            scn_no = 0
            current_req = True
            items.append(item(f'R:{source}#{req_no}', 'requirement', req.group(1), source, blob, delta))
            continue
        scn = SCN.match(line)
        if scn:
            if not current_req:
                raise ValueError(f'{source}: Requirementのない位置にScenarioがあります: {scn.group(1)}')
            scn_no += 1
            items.append(item(f'S:{source}#{req_no}.{scn_no}', 'scenario', scn.group(1), source, blob, delta))
    if pending_from is not None:
        raise ValueError(f'{source}: FROM「{pending_from}」に対応するTOがありません')
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='pr-openspec: 監査対象のspecデルタから全要求台帳を作る')
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--head', required=True)
    parser.add_argument('--change', required=True)
    args = parser.parse_args(argv)
    try:
        head_sha = git(args.root, 'rev-parse', '--verify', f'{args.head}^{{commit}}').strip()
        listing = git(args.root, 'ls-tree', '-r', head_sha, '--', f'openspec/changes/{args.change}/specs')
        ledger: list[dict] = []
        for line in sorted(listing.splitlines()):
            meta, path = line.split('\t', 1)
            if not path.endswith('/spec.md'):
                continue
            blob = meta.split()[2]
            ledger.extend(parse(git(args.root, 'show', f'{head_sha}:{path}'), path, blob))
    except (subprocess.CalledProcessError, ValueError) as exc:
        print(json.dumps({'result': 'USAGE', 'error': str(exc)}, ensure_ascii=False))
        return 3
    print(json.dumps({'head_sha': head_sha, 'ledger': ledger}, ensure_ascii=False, indent=2))
    return 0 if ledger else 2


if __name__ == '__main__':
    sys.exit(main())
