"""クラウドが書く一つのMarkdownの限定文法と検査。"""
from __future__ import annotations

import re
import json
from .store import header

CONTRACT = "unified-qa-review-v1"
LABELS = {
    "契約": "contract", "依頼ID": "id", "リポジトリ": "repository", "開発ブランチ": "branch",
    "初回基準SHA": "initial_baseline", "差分基準SHA": "baseline", "対象SHA": "reviewed",
    "サイクル": "cycle", "要件指紋": "requirements_hash", "担当": "actor", "実行経路": "execution",
    "提出版": "version", "訂正ID": "correction_id", "置換元SHA256": "replaces", "保存先": "path",
    "結論": "gate", "必須確認": "required_checks",
}
FINDING_FIELDS = ["種別", "重大度", "状態", "要求対応", "根拠", "影響", "対応案", "対象", "完了条件", "検証方法"]
SECTIONS = ["識別", "参照資材の検証", "確認範囲", "受入基準の照合", "実施した検証", "未検証事項", "指摘", "実施側タスク", "前回指摘の再確認", "残余事項"]
CRITERION_LINE = re.compile(r"- (AC-\d{3}): (.*?) \| 判定: (PASS|FAIL|UNVERIFIED) \| 根拠: (.+)")


def visible_lines(raw: str):
    fence = None
    for line in raw.splitlines():
        m = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if m:
            mark = m.group(1)
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence):
                fence = None
            continue
        if fence or line.startswith((">", "    ", "\t")):
            continue
        yield line


def parse(raw: str) -> tuple[dict, list[str]]:
    data = {"findings": [], "tasks": [], "previous": {}, "criteria": [], "materials": [], "checks": [], "sections": {}}
    issues = []; section = None; finding = None
    for line in visible_lines(raw):
        if line.startswith("## "):
            section = line[3:].strip(); finding = None
            if section in data["sections"]:
                issues.append(f"見出しが重複: {section}")
            data["sections"].setdefault(section, [])
            continue
        if section:
            data["sections"][section].append(line)
        if section == "受入基準の照合":
            criterion = CRITERION_LINE.fullmatch(line)
            if criterion:
                criterion_id, text, result, evidence = criterion.groups()
                data["criteria"].append({"id": criterion_id, "text": text, "result": result, "evidence": evidence.strip()})
            elif line.startswith("- AC-"):
                issues.append("受入基準の記載形式が不正です")
        elif section == "参照資材の検証":
            material = re.fullmatch(r"- ([^:]+): SHA256:([0-9a-f]{64}|不足)", line)
            if material:
                data["materials"].append({"path": material.group(1), "sha256": material.group(2)})
        elif section == "実施した検証":
            check = re.fullmatch(r"- (CHECK-[A-Z0-9_-]+): (\{.*\})", line)
            if check:
                try:
                    payload = json.loads(check.group(2))
                    if not isinstance(payload, dict): raise ValueError("object required")
                    payload["id"] = check.group(1)
                    data["checks"].append(payload)
                except (json.JSONDecodeError, ValueError):
                    issues.append(f"check EvidenceのJSONが不正: {check.group(1)}")
        elif section == "実施側タスク":
            task = re.fullmatch(r"- (T-\d{2,}): Finding=(QA-[A-Za-z0-9_-]+); path=([^;]+); action=(.+); done_when=(.+); verify=(.+)", line)
            if task:
                task_id, finding_id, path, action, done_when, verify = task.groups()
                data["tasks"].append({"id": task_id, "finding": finding_id, "path": path.strip(), "action": action.strip(), "done_when": done_when.strip(), "verify": verify.strip()})
            elif line.startswith("- T-"):
                issues.append("実施側タスクの記載形式が不正です")
        m = re.fullmatch(r"### 指摘 ([A-Za-z0-9_-]+)", line)
        if m and section == "指摘":
            finding = {"id": m.group(1)}; data["findings"].append(finding); continue
        item = re.fullmatch(r"- ([^:]+):\s*(.+)", line)
        if not item:
            continue
        label, value = item.groups(); value = value.strip()
        if section == "識別":
            key = LABELS.get(label)
            if key:
                if key in data: issues.append(f"識別項目が重複: {label}")
                else: data[key] = value
        elif finding and section == "指摘" and label in FINDING_FIELDS:
            if label in finding: issues.append(f"指摘項目が重複: {finding['id']} {label}")
            else: finding[label] = value
        elif section == "前回指摘の再確認" and label != "対象":
            if label in data["previous"]: issues.append(f"前回指摘IDが重複: {label}")
            else:
                parts = value.split(" | ", 1)
                data["previous"][label] = {"result": parts[0], "evidence": parts[1] if len(parts) == 2 else ""}
    for label, key in LABELS.items():
        if key not in data: issues.append(f"識別項目が不足: {label}")
    for section in SECTIONS:
        if not any(l.strip() for l in data["sections"].get(section, [])):
            issues.append(f"見出しまたは内容が不足: {section}")
    visible = "\n".join(visible_lines(raw))
    for label in ["created", "update"]:
        if not re.search(rf"^{label}: \d{{4}}-\d{{2}}-\d{{2}} \d{{2}}:\d{{2}} \(JST\)$", visible, re.M): issues.append(f"JSTメタデータが不足: {label}")
    if not re.search(r"^author: .+\(.+\)$", visible, re.M): issues.append("実際のツール・モデルのauthorが不足")
    if not raw.startswith("# ") or not raw.splitlines()[1:2] == [""]:
        issues.append("タイトルと空行の形式が不正")
    return data, issues


def check(raw: str, state: dict, expected: dict) -> tuple[dict, list[str]]:
    data, issues = parse(raw)
    expected_values = {k: str(state[k]) for k in ["id", "repository", "branch", "initial_baseline", "baseline", "reviewed", "cycle", "requirements_hash"]}
    expected_values.update(contract=CONTRACT, version=str(expected["version"]), correction_id=expected["correction_id"], replaces=expected["replaces"], path=expected["review_path"])
    for k, value in expected_values.items():
        if data.get(k) != value: issues.append(f"依頼との不一致: {k}")
    expected_criteria = [
        {"id": f"AC-{index:03d}", "text": text}
        for index, text in enumerate(state["criteria"], start=1)
    ]
    actual_criteria = [{"id": c["id"], "text": c["text"]} for c in data["criteria"]]
    if actual_criteria != expected_criteria:
        issues.append("全受入基準のID・原文・件数・順序が依頼と一致しません")
    criterion_ids = [c["id"] for c in data["criteria"]]
    if len(set(criterion_ids)) != len(criterion_ids):
        issues.append("受入基準IDが重複しています")
    for criterion in data["criteria"]:
        if criterion["result"] not in {"PASS", "FAIL", "UNVERIFIED"} or not criterion["evidence"].strip():
            issues.append(f"受入基準の判定または根拠が不足: {criterion['id']}")
    expected_materials = state.get("reviewer_materials", [])
    actual_materials = data["materials"]
    if actual_materials != expected_materials:
        issues.append("QA Skill・出力契約のパスとSHA-256が依頼と一致しません")
    if len({m["path"] for m in actual_materials}) != len(actual_materials):
        issues.append("参照資材のパスが重複しています")
    if any(m["sha256"] == "不足" for m in actual_materials) and data.get("gate") != "HOLD":
        issues.append("必須Reviewer資材が不足している場合はHOLDが必要です")
    if data.get("actor") in {state["implementer"], "別のレビュー担当名"} or data.get("execution") not in {"別チャット", "別担当", "クラウド"}:
        issues.append("実装チャットと分離した担当・実行経路を記録してください")
    if data.get("gate") not in {"PASS", "HOLD", "FAIL", "INCONCLUSIVE"}:
        issues.append("結論が不正")
    if data.get("required_checks") not in {"完了", "未完了"}:
        issues.append("必須確認の値が不正")
    expected_checks = state.get("checks", [])
    actual_checks = data["checks"]
    expected_ids = [c["id"] for c in expected_checks]
    actual_ids = [c.get("id") for c in actual_checks]
    if actual_ids != expected_ids or len(set(actual_ids)) != len(actual_ids):
        issues.append("実行checkの件数・ID・順序が依頼と一致しません")
    by_id = {c["id"]: c for c in expected_checks}
    for result in actual_checks:
        cid = result.get("id")
        contract = by_id.get(cid)
        if not contract: continue
        if result.get("status") not in {"PASS", "FAIL", "NOT_RUN", "ERROR"}:
            issues.append(f"check状態が不正: {cid}")
            continue
        for field in ["type", "argv", "cwd"]:
            if result.get(field, "command" if field == "type" else None) != contract.get(field, "command" if field == "type" else "."):
                issues.append(f"依頼checkとの不一致: {cid} {field}")
        if result.get("env") != contract.get("env", {}): issues.append(f"依頼checkとの不一致: {cid} env")
        if contract.get("type") == "python-version":
            if result.get("python_minimum") != contract["python_minimum"]: issues.append(f"依頼checkとの不一致: {cid} python_minimum")
            if result.get("status") in {"PASS", "FAIL"}:
                minimum = tuple(map(int, contract["python_minimum"].split(".")))
                match = re.search(r"Python\s+(\d+)\.(\d+)(?:\.\d+)?", str(result.get("runtime", "")))
                if not match:
                    issues.append(f"Python versionの観測Evidenceを解析できません: {cid}")
                elif result.get("status") == "PASS" and tuple(map(int, match.groups())) < minimum:
                    issues.append(f"Python versionが最低要件を満たしません: {cid}")
        if result.get("timeout_seconds") != contract.get("timeout_seconds"):
            issues.append(f"依頼checkとの不一致: {cid} timeout_seconds")
        if not isinstance(result.get("runtime"), str) or not result["runtime"].strip(): issues.append(f"実行環境の記録が不足: {cid}")
        if result["status"] in {"PASS", "FAIL"}:
            code = result.get("exit_code")
            if type(code) is not int: issues.append(f"exit codeが不足: {cid}")
            else:
                expected_codes = contract.get("expected_exit_codes", [0])
                matched = code in expected_codes
                runtime_ok = True
                if contract.get("type") == "python-version":
                    version_match = re.search(r"Python\s+(\d+)\.(\d+)(?:\.\d+)?", str(result.get("runtime", "")))
                    runtime_ok = bool(version_match and tuple(map(int, version_match.groups())) >= tuple(map(int, contract["python_minimum"].split("."))))
                if (result["status"] == "PASS") != (matched and runtime_ok): issues.append(f"statusと期待終了codeまたはruntimeが矛盾: {cid}")
            for key in ["stdout_sha256", "stderr_sha256"]:
                if not re.fullmatch(r"[0-9a-f]{64}", str(result.get(key, ""))): issues.append(f"{key}のEvidenceが不足または不正: {cid}")
            for key in ["stdout_excerpt", "stderr_excerpt"]:
                if not isinstance(result.get(key), str): issues.append(f"{key}の内容Evidenceがありません: {cid}")
            if type(result.get("output_truncated")) is not bool: issues.append(f"output_truncatedがありません: {cid}")
            if type(result.get("duration_ms")) is not int or result["duration_ms"] < 0:
                issues.append(f"所要時間Evidenceが不足または不正: {cid}")
        elif not isinstance(result.get("reason"), str) or not result["reason"].strip():
            issues.append(f"未実行・実行エラーの理由が不足: {cid}")
    required_results = {c.get("id"): c for c in actual_checks}
    required_failed = any(c.get("required") and required_results.get(c["id"], {}).get("status") == "FAIL" for c in expected_checks)
    required_incomplete = any(c.get("required") and required_results.get(c["id"], {}).get("status") in {"NOT_RUN", "ERROR", None} for c in expected_checks)
    criteria_failed = any(c["result"] == "FAIL" for c in data["criteria"])
    identity_fields = {"contract", "id", "repository", "branch", "initial_baseline", "baseline", "reviewed", "cycle", "requirements_hash", "version", "correction_id", "replaces", "path"}
    provenance_hold = (
        any(m["sha256"] == "不足" for m in actual_materials)
        or actual_materials != expected_materials
        or actual_criteria != expected_criteria
        or any(issue.startswith("QA Skill・出力契約のパスとSHA-256が") for issue in issues)
        or any(issue.startswith("依頼との不一致: ") and issue.split(": ", 1)[1] in identity_fields for issue in issues)
        or any(issue == "実装チャットと分離した担当・実行経路を記録してください" for issue in issues)
    )
    if required_incomplete and data.get("required_checks") == "完了":
        issues.append("未実施またはERRORの必須checkを完了にできません")
    # Priority is deterministic: identity/provenance HOLD, known FAIL, incomplete INCONCLUSIVE, then PASS.
    expected_gate = "HOLD" if provenance_hold else "FAIL" if (criteria_failed or required_failed) else "INCONCLUSIVE" if required_incomplete else None
    if expected_gate and data.get("gate") != expected_gate:
        issues.append(f"Gate優先順位に従い総合{expected_gate}が必要です")
    if required_incomplete and data.get("gate") not in {"FAIL", "HOLD", "INCONCLUSIVE"}:
        issues.append("環境不足などで必須checkが未完了のため総合INCONCLUSIVEが必要です")
    if data.get("gate") == "PASS" and data.get("required_checks") != "完了":
        issues.append("未完了の必須確認をPASSにできません")
    if data.get("gate") == "PASS" and any(c["result"] != "PASS" for c in data["criteria"]):
        issues.append("未達または未検証の受入基準があるためPASSにできません")
    ids = set()
    for f in data["findings"]:
        if f["id"] in ids: issues.append(f"指摘IDが重複: {f['id']}")
        ids.add(f["id"])
        for label in FINDING_FIELDS:
            if not f.get(label): issues.append(f"指摘項目が不足: {f['id']} {label}")
        if f.get("種別") not in {"要求未達", "不具合", "改善提案", "未検証"}: issues.append(f"種別が不正: {f['id']}")
        if f.get("重大度") not in {"重大", "通常", "軽微"}: issues.append(f"重大度が不正: {f['id']}")
        if f.get("状態") not in {"OPEN", "CLOSED"}: issues.append(f"状態が不正: {f['id']}")
        if f.get("根拠") and not re.search(r"[^\s:]+:\d+", f["根拠"]): issues.append(f"対象版の根拠パスと行が不足: {f['id']}")
        if f.get("状態") == "OPEN" and (f.get("重大度") == "重大" or f.get("種別") == "要求未達") and data.get("gate") == "PASS":
            issues.append(f"未解決の重要指摘とPASSが矛盾: {f['id']}")
    task_ids = set()
    finding_ids = {f["id"] for f in data["findings"]}
    for task in data["tasks"]:
        if task["id"] in task_ids: issues.append(f"実施側タスクIDが重複: {task['id']}")
        task_ids.add(task["id"])
        if task["finding"] not in finding_ids: issues.append(f"実施側タスクが未知Findingを参照: {task['id']}")
    tasked_findings = {task["finding"] for task in data["tasks"]}
    for finding in data["findings"]:
        if finding.get("状態") == "OPEN" and finding.get("種別") != "改善提案" and finding["id"] not in tasked_findings:
            issues.append(f"対応が必要なFindingに実施側タスクがありません: {finding['id']}")
    for fid in state["unresolved"]:
        previous = data["previous"].get(fid)
        placeholder = previous and re.search(r"(?:記載してください|根拠と確認方法を記載|確認結果を記載|TODO|TBD)", previous["evidence"], re.I)
        if not previous or not previous["evidence"] or placeholder or previous["result"] not in {"解消", "未解消", "未検証", "撤回提案"}:
            issues.append(f"前回指摘の再確認が不足: {fid}")
    return data, issues


def template(state: dict, author: str = "担当AI (実際のモデル名)", expected: dict | None = None) -> str:
    expected = expected or {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]}
    values = {k: state[k] for k in ["id", "repository", "branch", "initial_baseline", "baseline", "reviewed", "cycle", "requirements_hash"]}
    values.update(contract=CONTRACT, actor="別のレビュー担当名", execution="クラウド" if state["audience"] == "cloud" else "別チャット", version=expected["version"], correction_id=expected["correction_id"], replaces=expected["replaces"], path=expected["review_path"], gate="INCONCLUSIVE", required_checks="未完了")
    text = header("独立QAレビュー", author) + "## 識別\n\n"
    text += "\n".join(f"- {label}: {values[key]}" for label, key in LABELS.items())
    text += "\n\n## 確認範囲\n\n確認した対象版のファイルと要件、根拠を記載。\n\n## 実施した検証\n\n実行した方法・結果・根拠を記載。実行していない場合は「なし」。各指定checkについて、次のJSON行にargv、cwd、env、timeout、Python/tool runtime、status、exit_code、duration_ms、stdout/stderr excerpt、各SHA-256、output_truncatedを記録してください。statusはPASS/FAIL/NOT_RUN/ERRORです。\n"
    for check in state.get("checks", []):
        expected_check = {"type": check.get("type", "command"), "argv": check["argv"], "cwd": check.get("cwd", "."), "env": check.get("env", {}), "timeout_seconds": check["timeout_seconds"]}
        if check.get("type") == "python-version": expected_check["python_minimum"] = check["python_minimum"]
        placeholder = {**expected_check, "status": "NOT_RUN", "runtime": "Python/tool version", "reason": "未実行理由"}
        text += f"\n- {check['id']}: {json.dumps(placeholder, ensure_ascii=False, separators=(',', ':'))}"
    text += "\n\n## 未検証事項\n\n実行できなかった必須確認と理由を記載。ない場合は「なし」。\n\n## 指摘\n\n指摘がなければ「なし」。指摘がある場合は次のブロックを必要数追加。\n"
    text += "\n```markdown\n### 指摘 QA-F01\n" + "\n".join(f"- {label}: {value}" for label, value in zip(FINDING_FIELDS, ["要求未達", "重大", "OPEN", "受入基準の項目", "src/example.py:12 対象版での観測", "利用者への影響", "修正または確認の具体案", "src/example.py", "観察できる完了条件", "手順と期待結果"])) + "\n```\n"
    text += "\n## 実施側タスク\n\n修正や追加確認が必要なFindingごとに、細分化した実施タスクを追加し、Finding IDで結び付けてください。不要な場合は「なし」。\n\n"
    text += "\n## 前回指摘の再確認\n\n"
    text += "\n".join(f"- {fid}: 未検証 | 対象版の根拠と確認方法を記載" for fid in state["unresolved"]) if state["unresolved"] else "- 対象: なし"
    materials = state.get("reviewer_materials", [])
    text = text.replace("\n## 確認範囲\n", "\n## 参照資材の検証\n\n" + "\n".join(f"- {m['path']}: SHA256:{m['sha256']}" for m in materials) + "\n\n指定SHAのQA Skillと出力契約を読み、hashを照合してください。`不足`または不一致・取得不能の場合はGateをHOLDとし、その根拠を残してください。\n\n## 確認範囲\n")
    criterion_rows = "\n".join(
        f"- AC-{index:03d}: {criterion} | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載"
        for index, criterion in enumerate(state["criteria"], start=1)
    )
    text = text.replace("\n## 実施した検証\n", "\n## 受入基準の照合\n\n" + criterion_rows + "\n\n各行のID・基準原文・順序を保持し、判定と対象版の根拠を記載してください。\n\n## 実施した検証\n")
    return text + "\n\n## 残余事項\n\n改善提案、残る確認と返却参照を記載。ない場合は「なし」。\n"


def invite(state: dict) -> str:
    text = header("独立QAの依頼" if state["reviewed"] else "QA依頼の下書き：対象確定待ち", state["author"])
    if state["reviewed"] is None:
        text += "対象は未commitです。この下書きを正式依頼として渡さず、表示対象をローカルでcommitする指示、ユーザー作成commitの確認、またはクラウド公開の明示指示で対象を確定してください。\n\n"
    text += f"## 目的と受入基準\n\n{state['purpose']}\n\n前提: {state['assumptions']}\n\n" + "\n".join(f"- AC-{index:03d}: {criterion}" for index, criterion in enumerate(state["criteria"], start=1))
    text += f"\n\n## 対象と担当\n\nリポジトリ: {state['repository']}\n開発ブランチ: {state['branch']}\n初回基準: {state['initial_baseline']}\n差分基準: {state['baseline']}\n対象版: {state['reviewed'] or '未確定'}\n依頼ID: {state['id']}\nサイクル: {state['cycle']}\n\n実装担当 `{state['implementer']}` とは別の担当・チャットでレビューしてください。元要求との対応、修正差分と周辺影響、前回指摘を確認し、必要なら元実装にも遡ってください。\n"
    text += "\n## 差分の選別\n\n製品対象:\n" + "\n".join(f"- {p}" for p in state["products"])
    text += "\n\n登録済み運用成果物（製品差分から選別し、根拠として保持）:\n" + "\n".join(f"- {p}: {v}" for p, v in state["operational"].items())
    text += "\n\n対象外の判断:\n" + ("\n".join(f"- {p}: {why}" for p, why in state["excluded"].items()) or "なし")
    text += "\n\n初回基準からの差分と今回差分に同じ個別パスの選別を適用してください。DIR全体の除外、未分類パスの黙示的除外は行わず、改名は旧新パスを確認します。\n"
    text += "\n## 前回指摘と必要な検証\n\n" + ("\n".join(f"- {fid}: {value}" for fid, value in state["unresolved"].items()) or "前回指摘なし")
    checks = state.get("checks", [])
    text += "\n\n## 実行検証契約\n\n" + ("依頼に列挙したcheckは、対象SHAで利用可能な環境・規則の範囲内で実行してください。argv配列をshell経由で解釈せず実行し、環境構築のための無許可install、network、credential利用は行わないでください。Python等の製品検証ツールが利用可能なら実行し、QA管理CLIの導入は不要です。各結果はtype、status、runtime、argv、cwd、env、timeout、exit code、duration、stdout/stderr excerpt、完全な出力のSHA-256、excerpt切詰め有無を記録します。必須checkのFAILは総合FAIL、必須checkのNOT_RUN/ERRORはPASS不可です。環境不足は理由付きで未検証として残します。\n\n" + "\n".join(f"- {c['id']}（{c['type']}／{'必須' if c['required'] else '任意'}）: argv={json.dumps(c['argv'], ensure_ascii=False)}; cwd={c.get('cwd', '.')}; env={json.dumps(c.get('env', {}), ensure_ascii=False)}; timeout={c['timeout_seconds']}秒; expected_exit_codes={c.get('expected_exit_codes', [0])}" + (f"; Python minimum={c['python_minimum']}" if c.get('type') == "python-version" else "") for c in checks) if checks else "実行checkの指定はありません。対象環境で利用可能な場合は、受入基準に必要な製品テストを実行し、方法・環境・結果をEvidenceとして記録してください。")
    text += "\n## Reviewerが読むQA Skillと出力契約\n\n対象commitから以下のファイルを読み、記載hashを確認してください。不在、取得不能、またはhash不一致ならその理由をレビューへ記録し、GateをHOLDにしてください。実装担当AIの説明は根拠の代わりにせず、指摘・実施タスク・詳細なEvidenceは合意済み出力契約に従って記録してください。\n\n" + "\n".join(f"- `{m['path']}` — SHA-256: `{m['sha256']}`" for m in state.get("reviewer_materials", []))
    text += f"\n\n## 保存と返却\n\n変更してよいファイルは `{state['review_path']}` の日本語Markdown 1ファイルです。製品コード・依頼・管理状態は変更せず、指定先に結果を保存してください。Quality QA管理CLI・skill導入・JSONファイル作成は不要です。Pythonや既存の製品検証ツールは、対象リポジトリの規則と実行環境が許す場合に使用してください。指定ブランチが基本ですが、別ブランチ・PR・本文返却も可能です。取得元commitとパス、または本文返却であることを返信してください。レビュー成果物だけのtopic公開は依頼先の規則と許可に従い、main/masterへ統合しないでください。\n\n指摘0件でも確認範囲と根拠を記載し、必要な確認を実行できない場合は必須確認を未完了にして未検証事項へ残してください。重大未解決・要求未達とPASSを併記しないでください。\n\n## レビュー記載例\n\n````markdown\n"
    return text + template(state) + "\n````\n"
