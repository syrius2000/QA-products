"""旧blindの4成果物を変更せず、原依頼と照合して表示する。"""
from __future__ import annotations
import json
import re
from pathlib import Path
from .store import QAError, digest
from .review import visible_lines


def read_legacy(directory: Path, invite: Path) -> dict:
    names = ["01_review.md", "02_tasks.md", "03_machine.json", "STATUS.md"]
    if directory.is_symlink() or invite.is_symlink() or not invite.is_file():
        raise QAError("旧原文の通常ファイルを指定してください")
    files = {name: directory / name for name in names}
    if any(not p.is_file() or p.is_symlink() for p in files.values()):
        raise QAError("旧4成果物が揃っていません")
    raw = {name: p.read_bytes() for name, p in files.items()}
    try:
        machine = json.loads(raw["03_machine.json"])
        old_invite = invite.read_text(); md = raw["01_review.md"].decode(); tasks = raw["02_tasks.md"].decode()
        status = raw["STATUS.md"].decode().strip()
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise QAError("旧成果物を解釈できません") from e
    issues = []
    if not isinstance(machine, dict): raise QAError("旧機械JSONはオブジェクトが必要です")
    required = {"schema", "topic", "cycle", "baseline", "reviewed", "gate", "findings", "tasks"}
    if required - machine.keys() or machine.get("schema") != "blind-qa-cycle-v1": issues.append("旧機械JSONの必須項目が不足")
    if status != machine.get("gate") or status not in {"PASS", "HOLD", "FAIL", "INCONCLUSIVE"}: issues.append("STATUSと機械JSONのGateが不一致")
    def fields(text):
        result = {}
        for line in visible_lines(text):
            m = re.match(r"- ([^:]+):\s*(.*?)\s*$", line)
            if m:
                key, value = m.groups(); key=key.lower(); value=value.strip('`')
                if key in result: issues.append(f"旧識別項目が重複: {key}")
                result[key]=value
        return result
    original=fields(old_invite); review_fields=fields(md)
    for key in ["baseline", "reviewed", "cycle", "topic"]:
        if str(machine.get(key)) != original.get(key): issues.append(f"原依頼と旧結果が不一致／確認不能: {key}")
    for key in ["baseline", "reviewed"]:
        if not re.fullmatch(r"[0-9a-f]{40}", str(machine.get(key))): issues.append(f"旧完全SHAが不足: {key}")
        if review_fields.get(key) != machine.get(key): issues.append(f"旧レビューとJSONが不一致: {key}")
    if review_fields.get("gate") != status: issues.append("旧レビューのGateが不一致")
    findings=machine.get("findings",[]); tasks_json=machine.get("tasks",[])
    if not isinstance(findings,list) or not isinstance(tasks_json,list): raise QAError("旧指摘とタスクは配列が必要です")
    ids=[f.get('id') for f in findings if isinstance(f,dict)]
    if len(ids)!=len(findings) or len(set(ids))!=len(ids) or not all(isinstance(x,str) and x for x in ids): issues.append("旧指摘IDが不正または重複")
    for task in tasks_json:
        if not isinstance(task,dict) or task.get("closes") not in ids or not task.get("verify"): issues.append("未知指摘を参照する旧タスク、または検証方法不足")
        elif task.get("id") not in tasks or task.get("closes") not in tasks: issues.append("旧タスクMarkdownとの対応が不足")
    for f in findings:
        if not isinstance(f,dict): continue
        if f.get("severity") not in {"High","Medium","Low","PASS"} or f.get("status") not in {"OPEN","CLOSED"}: issues.append("旧指摘の重大度／状態が不正")
        if f.get("id") not in md: issues.append("旧レビューMarkdownに指摘がない")
        if f.get("severity")=="High" and f.get("status")=="OPEN":
            if status=="PASS": issues.append("未解決HighとPASSが矛盾")
            if not any(isinstance(t,dict) and t.get("closes")==f.get("id") for t in tasks_json): issues.append("Highへの修正タスクが不足")
    if not re.search(r"(?:## .*目的|## .*Purpose)", old_invite) or not re.search(r"(?:## .*受入基準|## .*Acceptance)", old_invite): issues.append("原依頼の目的・受入基準が確認不能")
    return {"schema":"legacy-read-only", "gate":status,"findings":findings,"tasks":tasks_json,"issues":issues,"valid":not issues,"source_hashes":{name:digest(value) for name,value in raw.items()},"invite_hash":digest(invite.read_bytes()),"next":{"担当":"ユーザー→旧レビュー担当","操作":"不足事項の確認" if issues else "元基準と実行Evidenceを確認して新運用へ引き継ぐ", "理由":"旧ファイルと正式caseは変更しません。旧PASSだけで新QAの完了を証明しません"}}
