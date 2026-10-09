from __future__ import annotations

import subprocess
import tempfile
import unittest
import base64
import json
import threading
import time
from pathlib import Path

from qa_workflow import review
from qa_workflow.store import QAError
from qa_workflow.workflow import verify_submission_snapshot


def record_user_prompt(repository: Path, prompt: str) -> None:
    with (repository / ".git" / "qa-user-prompts.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({"prompt": prompt}, ensure_ascii=False) + "\n")


def review_state() -> dict:
    return {
        "id": "QA-001",
        "repository": "owner/repo",
        "branch": "topic/qa",
        "initial_baseline": "1" * 40,
        "baseline": "2" * 40,
        "reviewed": "3" * 40,
        "cycle": 1,
        "requirements_hash": "a" * 64,
        "criteria": ["欠落行を検出する", "依頼との全文一致を検証する"],
        "reviewer_materials": [
            {"path": "quality-loop/skills/quality-qa/SKILL.md", "sha256": "b" * 64},
            {"path": "quality-loop/skills/quality-qa/references/reviewer_contract.md", "sha256": "c" * 64},
        ],
        "audience": "cloud",
        "implementer": "Implementer A",
        "unresolved": {},
        "review_path": "docs/Artifacts/qa_review_001_1004.md",
    }


def valid_review() -> str:
    state = review_state()
    text = review.template(state, author="Codex (GPT-6)")
    text = text.replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer B")
    return text


class AcceptanceCriteriaContractTests(unittest.TestCase):
    def test_all_criteria_and_pinned_skill_materials_are_accepted(self):
        state = review_state()
        parsed, issues = review.check(
            valid_review(),
            state,
            {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]},
        )
        self.assertEqual([], issues)
        self.assertEqual(state["criteria"], [item["text"] for item in parsed["criteria"]])

    def test_distributed_static_template_satisfies_the_same_parser_contract(self):
        state = review_state()
        state["checks"] = [{"id": "CHECK-PYTEST", "type": "command", "required": True, "argv": ["pytest", "tests"], "cwd": ".", "env": {}, "timeout_seconds": 120, "expected_exit_codes": [0]}]
        path = Path(__file__).resolve().parents[1] / "skills/quality-qa/templates/qa_review.md"
        text = path.read_text()
        substitutions = {
            "QA-NNN": state["id"], "OWNER/REPOSITORY": state["repository"], "TOPIC_BRANCH": state["branch"],
            "INITIAL_FULL_SHA": state["initial_baseline"], "BASELINE_FULL_SHA": state["baseline"],
            "REVIEWED_FULL_SHA": state["reviewed"], "REQUIREMENTS_SHA256": state["requirements_hash"],
            "docs/Artifacts/qa_review_NNN_MMDD.md": state["review_path"],
            "REVIEWER_NAME": "Reviewer B",
        }
        for placeholder, value in substitutions.items():
            text = text.replace(placeholder, value)
        for material in state["reviewer_materials"]:
            text = text.replace(f"{material['path']}: SHA256:EXPECTED_HASH", f"{material['path']}: SHA256:{material['sha256']}")
        _, issues = review.check(text, state, {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]})
        self.assertEqual([], issues)

    def test_omitted_changed_duplicated_extra_and_reordered_criteria_are_rejected(self):
        state = review_state()
        cases = {
            "omitted": lambda text: text.replace(
                "- AC-002: 依頼との全文一致を検証する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載\n", ""
            ),
            "changed": lambda text: text.replace("AC-001: 欠落行を検出する", "AC-001: 欠落行だけを検出する"),
            "duplicated": lambda text: text.replace(
                "- AC-002: 依頼との全文一致を検証する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
                "- AC-001: 欠落行を検出する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載\n- AC-002: 依頼との全文一致を検証する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
            ),
            "extra": lambda text: text.replace(
                "各行のID・基準原文・順序を保持", "- AC-003: 追加基準 | 判定: PASS | 根拠: extra.py:1\n\n各行のID・基準原文・順序を保持"
            ),
            "reordered": lambda text: text.replace(
                "- AC-001: 欠落行を検出する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載\n- AC-002: 依頼との全文一致を検証する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
                "- AC-002: 依頼との全文一致を検証する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載\n- AC-001: 欠落行を検出する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
            ),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                _, issues = review.check(
                    mutate(valid_review()),
                    state,
                    {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]},
                )
                self.assertTrue(any("受入基準" in issue for issue in issues), issues)

    def test_skill_hash_substitution_is_rejected(self):
        state = review_state()
        text = valid_review().replace("SHA256:" + "b" * 64, "SHA256:" + "e" * 64)
        _, issues = review.check(
            text,
            state,
            {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]},
        )
        self.assertTrue(any("Skill" in issue for issue in issues), issues)

    def test_required_check_evidence_is_tied_to_argv_and_runtime(self):
        state = review_state()
        state["checks"] = [{
            "id": "CHECK-PYTEST", "type": "command", "required": True,
            "argv": ["python", "-m", "pytest", "tests"], "cwd": "quality-loop",
            "env": {"PYTHONDONTWRITEBYTECODE": "1"}, "timeout_seconds": 120,
            "expected_exit_codes": [0],
        }]
        text = review.template(state, author="Codex (GPT-6)").replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer B")
        text = text.replace("- 結論: INCONCLUSIVE", "- 結論: PASS").replace("- 必須確認: 未完了", "- 必須確認: 完了")
        text = text.replace("- AC-001: 欠落行を検出する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載", "- AC-001: 欠落行を検出する | 判定: PASS | 根拠: src/a.py:1 検証成功")
        text = text.replace("- AC-002: 依頼との全文一致を検証する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載", "- AC-002: 依頼との全文一致を検証する | 判定: PASS | 根拠: src/a.py:2 検証成功")
        text = text.replace('{"type":"command","argv":["python","-m","pytest","tests"],"cwd":"quality-loop","env":{"PYTHONDONTWRITEBYTECODE":"1"},"timeout_seconds":120,"status":"NOT_RUN","runtime":"Python/tool version","reason":"未実行理由"}', '{"status":"PASS","type":"command","argv":["python","-m","pytest","tests"],"cwd":"quality-loop","env":{"PYTHONDONTWRITEBYTECODE":"1"},"timeout_seconds":120,"runtime":"Python 3.12 / pytest 8","exit_code":0,"duration_ms":1234,"stdout_sha256":"' + "e" * 64 + '","stderr_sha256":"' + "f" * 64 + '","stdout_excerpt":"all tests passed","stderr_excerpt":"","output_truncated":false}')
        _, issues = review.check(
            text, state,
            {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]},
        )
        self.assertEqual([], issues)
        state["checks"][0]["required"] = False
        text = review.template(state, author="Codex (GPT-6)").replace(
            "- 担当: 別のレビュー担当名", "- 担当: Reviewer B"
        ).replace("- 結論: INCONCLUSIVE", "- 結論: PASS").replace(
            "- 必須確認: 未完了", "- 必須確認: 完了"
        ).replace(
            "- AC-001: 欠落行を検出する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
            "- AC-001: 欠落行を検出する | 判定: PASS | 根拠: src/a.py:1 確認済み",
        ).replace(
            "- AC-002: 依頼との全文一致を検証する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
            "- AC-002: 依頼との全文一致を検証する | 判定: PASS | 根拠: src/a.py:2 確認済み",
        )
        _, issues = review.check(
            text, state,
            {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]},
        )
        self.assertEqual([], issues)

    def test_required_check_failure_cannot_be_reported_as_pass(self):
        state = review_state()
        state["checks"] = [{"id": "CHECK-TEST", "type": "command", "required": True, "argv": ["pytest"], "cwd": ".", "env": {}, "timeout_seconds": 60, "expected_exit_codes": [0]}]
        text = review.template(state, author="Codex (GPT-6)").replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer B")
        text = text.replace("- 結論: INCONCLUSIVE", "- 結論: PASS").replace("- 必須確認: 未完了", "- 必須確認: 完了")
        text = text.replace('{"type":"command","argv":["pytest"],"cwd":".","env":{},"timeout_seconds":60,"status":"NOT_RUN","runtime":"Python/tool version","reason":"未実行理由"}', '{"status":"FAIL","type":"command","argv":["pytest"],"cwd":".","env":{},"timeout_seconds":60,"runtime":"pytest 8","exit_code":1,"duration_ms":10,"stdout_sha256":"' + "e" * 64 + '","stderr_sha256":"' + "f" * 64 + '","stdout_excerpt":"failed","stderr_excerpt":"failure detail","output_truncated":false}')
        _, issues = review.check(text, state, {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]})
        self.assertTrue(any("総合FAIL" in issue for issue in issues), issues)

    def test_required_check_environment_gap_is_inconclusive(self):
        state = review_state()
        state["checks"] = [{"id": "CHECK-TEST", "type": "python-version", "python_minimum": "3.10", "required": True, "argv": ["python", "--version"], "cwd": ".", "env": {}, "timeout_seconds": 60, "expected_exit_codes": [0]}]
        text = review.template(state, author="Codex (GPT-6)").replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer B")
        _, issues = review.check(text, state, {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]})
        self.assertEqual([], issues)
        _, issues = review.check(text.replace("- 結論: INCONCLUSIVE", "- 結論: HOLD"), state, {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]})
        self.assertTrue(any("総合INCONCLUSIVE" in issue for issue in issues), issues)

    def test_required_tool_error_stays_inconclusive_and_optional_not_run_does_not_block_pass(self):
        state = review_state()
        state["checks"] = [{
            "id": "CHECK-CLI", "type": "command", "required": True,
            "argv": ["pytest", "tests"], "cwd": ".", "env": {},
            "timeout_seconds": 60, "expected_exit_codes": [0],
        }]
        text = review.template(state, author="Codex (GPT-6)").replace(
            "- 担当: 別のレビュー担当名", "- 担当: Reviewer B"
        )
        marker = "- CHECK-CLI: "
        line = next(item for item in text.splitlines() if item.startswith(marker))
        result = json.loads(line[len(marker):])
        result.update(status="ERROR", runtime="Python 3.14.7", reason="pytest executable is unavailable")
        text = text.replace(line, marker + json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        _, issues = review.check(
            text, state,
            {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]},
        )
        self.assertEqual([], issues)
        state["checks"][0]["required"] = False
        optional = review.template(state, author="Codex (GPT-6)").replace(
            "- 担当: 別のレビュー担当名", "- 担当: Reviewer B"
        ).replace("- 結論: INCONCLUSIVE", "- 結論: PASS").replace(
            "- 必須確認: 未完了", "- 必須確認: 完了"
        ).replace(
            "- AC-001: 欠落行を検出する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
            "- AC-001: 欠落行を検出する | 判定: PASS | 根拠: src/a.py:1 確認済み",
        ).replace(
            "- AC-002: 依頼との全文一致を検証する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
            "- AC-002: 依頼との全文一致を検証する | 判定: PASS | 根拠: src/a.py:2 確認済み",
        )
        _, issues = review.check(optional, state, {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]})
        self.assertEqual([], issues)

    def test_gate_precedence_keeps_known_failure_when_another_required_check_is_incomplete(self):
        state = review_state()
        state["checks"] = [
            {"id": "CHECK-FAIL", "type": "command", "required": True, "argv": ["test"], "cwd": ".", "env": {}, "timeout_seconds": 10, "expected_exit_codes": [0]},
            {"id": "CHECK-LATER", "type": "command", "required": True, "argv": ["test2"], "cwd": ".", "env": {}, "timeout_seconds": 10, "expected_exit_codes": [0]},
        ]
        text = review.template(state, author="Codex (GPT-6)").replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer B").replace("- 結論: INCONCLUSIVE", "- 結論: FAIL")
        lines = []
        for line in text.splitlines():
            if line.startswith("- CHECK-FAIL: "):
                payload = json.loads(line.split(": ", 1)[1]); payload.update(status="FAIL", runtime="pytest 9", exit_code=1, duration_ms=10, stdout_sha256="e"*64, stderr_sha256="f"*64, stdout_excerpt="failed", stderr_excerpt="", output_truncated=False); line = "- CHECK-FAIL: " + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            lines.append(line)
        parsed, issues = review.check("\n".join(lines), state, {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]})
        self.assertEqual([], issues)
        self.assertEqual("FAIL", parsed["gate"])

    def test_criterion_failure_and_required_check_error_is_fail_not_inconclusive(self):
        state = review_state()
        state["checks"] = [{"id": "CHECK-ERR", "type": "command", "required": True, "argv": ["pytest"], "cwd": ".", "env": {}, "timeout_seconds": 10, "expected_exit_codes": [0]}]
        text = review.template(state, author="Codex (GPT-6)").replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer B").replace("- 結論: INCONCLUSIVE", "- 結論: FAIL")
        text = text.replace("- AC-001: 欠落行を検出する | 判定: UNVERIFIED", "- AC-001: 欠落行を検出する | 判定: FAIL")
        marker = next(line for line in text.splitlines() if line.startswith("- CHECK-ERR: "))
        payload = json.loads(marker.split(": ", 1)[1]); payload.update(status="ERROR", runtime="pytest unavailable", reason="pytest unavailable")
        text = text.replace(marker, "- CHECK-ERR: " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        _, issues = review.check(text, state, {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]})
        self.assertEqual([], issues)

    def test_material_provenance_mismatch_takes_hold_priority_over_required_not_run(self):
        state = review_state()
        state["checks"] = [{"id": "CHECK-ENV", "type": "command", "required": True, "argv": ["pytest"], "cwd": ".", "env": {}, "timeout_seconds": 10, "expected_exit_codes": [0]}]
        text = review.template(state, author="Codex (GPT-6)").replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer B").replace("- 結論: INCONCLUSIVE", "- 結論: HOLD")
        text = text.replace("SHA256:" + "b" * 64, "SHA256:" + "e" * 64)
        parsed, issues = review.check(text, state, {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]})
        self.assertEqual("HOLD", parsed["gate"])
        self.assertFalse(any("Gate優先順位" in issue for issue in issues), issues)

    def test_python_version_check_rejects_runtime_below_contract(self):
        state = review_state()
        state["checks"] = [{"id": "CHECK-PYTHON", "type": "python-version", "python_minimum": "3.10", "required": True, "argv": ["python", "--version"], "cwd": ".", "env": {}, "timeout_seconds": 10, "expected_exit_codes": [0]}]
        text = review.template(state, author="Codex (GPT-6)").replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer B")
        text = text.replace("- 結論: INCONCLUSIVE", "- 結論: PASS").replace("- 必須確認: 未完了", "- 必須確認: 完了")
        text = text.replace('{"type":"python-version","argv":["python","--version"],"cwd":".","env":{},"timeout_seconds":10,"python_minimum":"3.10","status":"NOT_RUN","runtime":"Python/tool version","reason":"未実行理由"}', '{"status":"PASS","type":"python-version","argv":["python","--version"],"cwd":".","env":{},"timeout_seconds":10,"python_minimum":"3.10","runtime":"Python 3.9.18","exit_code":0,"duration_ms":1,"stdout_sha256":"' + "e" * 64 + '","stderr_sha256":"' + "f" * 64 + '","stdout_excerpt":"Python 3.9.18","stderr_excerpt":"","output_truncated":false}')
        _, issues = review.check(text, state, {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]})
        self.assertTrue(any("最低要件を満たしません" in issue for issue in issues), issues)

    def test_implementation_tasks_are_linked_to_findings(self):
        state = review_state()
        text = valid_review().replace(
            "修正や追加確認が必要なFindingごとに、細分化した実施タスクを追加し、Finding IDで結び付けてください。不要な場合は「なし」。",
            "- T-01: Finding=QA-F01; path=src/a.py; action=境界条件を修正; done_when=回帰例が成功; verify=pytest tests/test_a.py",
        ).replace(
            "\n## 実施側タスク\n",
            "\n### 指摘 QA-F01\n" + "\n".join([
                "- 種別: 不具合", "- 重大度: 通常", "- 状態: OPEN", "- 要求対応: 検査を修正",
                "- 根拠: src/a.py:12 再現", "- 影響: 誤判定", "- 対応案: 境界条件を確認",
                "- 対象: src/a.py", "- 完了条件: 再現例がpass", "- 検証方法: pytestで再現確認",
            ]) + "\n\n## 実施側タスク\n"
        )
        parsed, issues = review.check(text, state, {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]})
        self.assertEqual([], issues)
        self.assertEqual("QA-F01", parsed["tasks"][0]["finding"])

    def test_previous_finding_cannot_be_omitted_or_closed_without_evidence(self):
        state = review_state()
        state["unresolved"] = {"QA-F07": {"種別": "不具合", "根拠": "src/a.py:7"}}
        text = review.template(state, author="Codex (GPT-6)").replace(
            "- 担当: 別のレビュー担当名", "- 担当: Reviewer B"
        )
        _, issues = review.check(
            text, state,
            {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]},
        )
        self.assertTrue(any("前回指摘の再確認が不足: QA-F07" in issue for issue in issues), issues)
        text = text.replace(
            "- QA-F07: 未検証 | 対象版の根拠と確認方法を記載",
            "- QA-F07: 解消 | 対象SHAのsrc/a.py:7を確認し、再現テストが成功",
        )
        _, issues = review.check(
            text, state,
            {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]},
        )
        self.assertEqual([], issues)

    def test_open_finding_without_task_and_critical_pass_are_rejected(self):
        state = review_state()
        text = valid_review().replace("- 結論: INCONCLUSIVE", "- 結論: PASS").replace(
            "- 必須確認: 未完了", "- 必須確認: 完了"
        ).replace(
            "- AC-001: 欠落行を検出する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
            "- AC-001: 欠落行を検出する | 判定: PASS | 根拠: src/a.py:1 確認済み",
        ).replace(
            "- AC-002: 依頼との全文一致を検証する | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
            "- AC-002: 依頼との全文一致を検証する | 判定: PASS | 根拠: src/a.py:2 確認済み",
        )
        finding = "\n### 指摘 QA-F08\n" + "\n".join([
            "- 種別: 要求未達", "- 重大度: 重大", "- 状態: OPEN",
            "- 要求対応: 全基準を満たす", "- 根拠: src/a.py:9 再現",
            "- 影響: 受入不能", "- 対応案: 実装を修正", "- 対象: src/a.py",
            "- 完了条件: 再現しない", "- 検証方法: pytestで確認",
        ]) + "\n"
        text = text.replace("\n## 実施側タスク\n", finding + "\n## 実施側タスク\n")
        _, issues = review.check(
            text, state,
            {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": state["review_path"]},
        )
        self.assertTrue(any("未解決の重要指摘とPASSが矛盾" in issue for issue in issues), issues)
        self.assertTrue(any("実施側タスクがありません" in issue for issue in issues), issues)


class SubmittedSnapshotBoundaryTests(unittest.TestCase):
    def run_git(self, root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
        )
        return result.stdout.strip()

    def test_changes_to_another_product_after_submit_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_git(root, "init", "-b", "topic/qa")
            self.run_git(root, "config", "user.name", "QA Test")
            self.run_git(root, "config", "user.email", "qa@example.invalid")
            (root / "product-a.txt").write_text("submitted A\n")
            (root / "product-b.txt").write_text("submitted B\n")
            self.run_git(root, "add", "product-a.txt", "product-b.txt")
            self.run_git(root, "commit", "-m", "submitted snapshot")
            state = {
                "products": {"product-a.txt": "製品", "product-b.txt": "製品"},
                "plan": {"paths": ["product-a.txt"]},
                "submission": {
                    "product_paths": ["product-a.txt", "product-b.txt"],
                    "product_snapshot": {
                        "product-a.txt": {"mode": "100644", "hash": "0" * 64},
                        "product-b.txt": {"mode": "100644", "hash": "0" * 64},
                    }
                },
            }
            from qa_workflow import gitops

            state["submission"]["product_snapshot"] = gitops.snapshot(
                root, ["product-a.txt", "product-b.txt"]
            )
            verify_submission_snapshot(root, state)
            (root / "product-b.txt").write_text("unapproved later edit\n")
            with self.assertRaisesRegex(QAError, "修正提出後に製品対象が変更"):
                verify_submission_snapshot(root, state)


class GitPreflightTests(unittest.TestCase):
    def run_git(self, root: Path, *args: str) -> str:
        result = subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
        return result.stdout.strip()

    def test_preflight_reports_dirty_paths_without_changing_them(self):
        from qa_workflow.gitops import status_preflight

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_git(root, "init", "-b", "topic/qa")
            self.run_git(root, "config", "user.name", "QA Test")
            self.run_git(root, "config", "user.email", "qa@example.invalid")
            self.run_git(root, "remote", "add", "origin", "https://github.com/example/repo.git")
            self.run_git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
            (root / "tracked.txt").write_text("base\n")
            self.run_git(root, "add", "tracked.txt")
            self.run_git(root, "commit", "-m", "base")
            (root / "tracked.txt").write_text("staged\n")
            self.run_git(root, "add", "tracked.txt")
            (root / "tracked.txt").write_text("unstaged\n")
            (root / "new.txt").write_text("untracked\n")
            before = self.run_git(root, "status", "--porcelain=v1", "-z")
            result = status_preflight(root)
            after = self.run_git(root, "status", "--porcelain=v1", "-z")
            self.assertEqual(before, after)
            self.assertEqual(["tracked.txt"], result["staged"])
            self.assertEqual(["tracked.txt"], result["unstaged"])
            self.assertEqual(["new.txt"], result["untracked"])
            self.assertFalse(result["clean"])
            self.assertFalse(result["safe_to_implement"])

    def test_clean_topic_branch_is_safe_to_begin(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from qa_workflow.cli import main
        from qa_workflow.gitops import status_preflight

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_git(root, "init", "-b", "main")
            self.run_git(root, "config", "user.name", "QA Test")
            self.run_git(root, "config", "user.email", "qa@example.invalid")
            self.run_git(root, "remote", "add", "origin", "https://github.com/example/repo.git")
            self.run_git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
            (root / "tracked.txt").write_text("base\n")
            self.run_git(root, "add", "tracked.txt")
            self.run_git(root, "commit", "-m", "base")
            self.run_git(root, "switch", "-c", "topic/qa")
            result = status_preflight(root)
            self.assertTrue(result["clean"])
            self.assertTrue(result["safe_to_implement"])
            output = StringIO()
            with redirect_stdout(output):
                exit_code = main(["--root", str(root), "preflight"])
            self.assertEqual(0, exit_code)
            self.assertIn("Git preflight: clean", output.getvalue())
            self.assertIn("実装可能: はい", output.getvalue())

    def test_path_classification_preserves_product_operational_excluded_and_rename_sides(self):
        from qa_workflow import gitops

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_git(root, "init", "-b", "topic/qa")
            self.run_git(root, "config", "user.name", "QA Test")
            self.run_git(root, "config", "user.email", "qa@example.invalid")
            (root / "docs").mkdir()
            (root / "docs/old.md").write_text("product requirement\n")
            self.run_git(root, "add", "docs/old.md")
            self.run_git(root, "commit", "-m", "base")
            initial = gitops.sha(root, "HEAD")
            self.run_git(root, "mv", "docs/old.md", "docs/new.md")
            (root / "docs/state.json").write_text("{}\n")
            (root / "docs/excluded.md").write_text("reasoned out of scope\n")
            self.run_git(root, "add", "docs/state.json", "docs/excluded.md")
            self.run_git(root, "commit", "-m", "rename and add artifacts")
            target = gitops.sha(root, "HEAD")
            result = gitops.classify(
                root, initial, initial, target,
                {"docs/old.md": "製品", "docs/new.md": "製品"},
                {"docs/state.json": "運用"},
                {"docs/excluded.md": "QA対象外の判断"},
            )
            self.assertEqual(["docs/new.md", "docs/old.md"], result["initial"]["product"])
            self.assertEqual(["docs/state.json"], result["initial"]["operational"])
            self.assertEqual({"docs/excluded.md": "QA対象外の判断"}, result["initial"]["excluded"])


class AtomicStoreTests(unittest.TestCase):
    def test_atomic_replace_failure_preserves_previous_file_and_removes_temp(self):
        from unittest.mock import patch
        from qa_workflow.store import atomic

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "record.md"
            target.write_bytes(b"previous complete record")
            with patch("qa_workflow.store.os.replace", side_effect=OSError("simulated replace failure")):
                with self.assertRaisesRegex(OSError, "simulated replace failure"):
                    atomic(target, b"partial replacement")
            self.assertEqual(b"previous complete record", target.read_bytes())
            self.assertEqual([target], list(Path(tmp).iterdir()))

    def test_file_lock_serializes_mutating_transactions(self):
        from qa_workflow.store import Store

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git_dir = root / ".git"
            git_dir.mkdir()
            store = Store(root, git_dir)
            events = []

            def worker(label):
                with store.transaction():
                    events.append((label, "start"))
                    time.sleep(0.03)
                    events.append((label, "end"))

            first = threading.Thread(target=worker, args=("A",))
            second = threading.Thread(target=worker, args=("B",))
            first.start(); second.start(); first.join(); second.join()
            self.assertEqual(4, len(events))
            self.assertEqual(events[0][0], events[1][0])
            self.assertEqual(events[0][1], "start")
            self.assertEqual(events[1][1], "end")
            self.assertEqual(events[2][1], "start")
            self.assertEqual(events[3][1], "end")


class GitHubAcquisitionTests(unittest.TestCase):
    def make_gh(self, directory: Path, *, file_type="file", path="docs/qa_review.md") -> tuple[Path, Path]:
        executable = directory / "gh-fixture"
        log = directory / "calls.json"
        sha = "a" * 40
        content = base64.b64encode(b"# review\n").decode()
        source = f'''#!/usr/bin/env python3
import json, pathlib, sys
args=sys.argv[1:]
log=pathlib.Path({str(log)!r})
calls=json.loads(log.read_text()) if log.exists() else []
calls.append(args)
log.write_text(json.dumps(calls))
if args[0] == "pr":
    result={{"headRefOid":"{sha}","headRefName":"topic/review","headRepository":{{"name":"project"}},"headRepositoryOwner":{{"login":"fork"}}}}
elif "commits" in args[1]:
    result={{"sha":"{sha}"}}
else:
    result={{"type":{file_type!r},"path":{path!r},"encoding":"base64","content":{content!r}}}
print(json.dumps(result))
'''
        executable.write_text(source)
        executable.chmod(0o755)
        return executable, log

    def test_branch_acquisition_pins_content_to_resolved_sha(self):
        from qa_workflow.github import GitHub

        with tempfile.TemporaryDirectory() as tmp:
            executable, log = self.make_gh(Path(tmp))
            body, source = GitHub(str(executable)).acquire("owner/project", "docs/qa_review.md", branch="topic/review")
            calls = json.loads(log.read_text())
            self.assertEqual(b"# review\n", body)
            self.assertEqual("a" * 40, source["commit"])
            self.assertIn(f"repos/owner/project/contents/docs/qa_review.md?ref={'a' * 40}", calls[-1][1])

    def test_pull_request_acquisition_uses_fork_head_repository_and_sha(self):
        from qa_workflow.github import GitHub

        with tempfile.TemporaryDirectory() as tmp:
            executable, log = self.make_gh(Path(tmp))
            body, source = GitHub(str(executable)).acquire("owner/project", "docs/qa_review.md", pr="https://github.com/owner/project/pull/12")
            calls = json.loads(log.read_text())
            self.assertEqual(b"# review\n", body)
            self.assertEqual("fork/project", source["repository"])
            self.assertIn("repos/fork/project/contents/docs/qa_review.md?ref=" + "a" * 40, calls[-1][1])

    def test_non_markdown_target_is_rejected_without_acceptance(self):
        from qa_workflow.github import GitHub
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            executable, _ = self.make_gh(Path(tmp), file_type="symlink")
            with self.assertRaisesRegex(QAError, "通常Markdown"):
                GitHub(str(executable)).acquire("owner/project", "docs/qa_review.md", branch="topic/review")

    def test_github_authentication_failure_is_not_treated_as_success(self):
        from qa_workflow.github import GitHub
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            executable = Path(tmp) / "gh-denied"
            executable.write_text("#!/usr/bin/env python3\nimport sys\nprint('authentication required', file=sys.stderr)\nsys.exit(1)\n")
            executable.chmod(0o755)
            with self.assertRaisesRegex(QAError, "取得に失敗"):
                GitHub(str(executable)).acquire("owner/project", "docs/qa_review.md", branch="topic/review")


class ExecutionContractIntegrationTests(unittest.TestCase):
    def run_git(self, root: Path, *args: str) -> str:
        result = subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
        return result.stdout.strip()

    def setup_bare_remote(self, root: Path) -> tuple[Path, Path]:
        repository = root / "repo"
        remote = root / "remote.git"
        subprocess.run(["git", "init", "--bare", "-b", "master", str(remote)], check=True, capture_output=True)
        repository.mkdir()
        self.run_git(repository, "init", "-b", "master")
        self.run_git(repository, "config", "user.name", "QA Test")
        self.run_git(repository, "config", "user.email", "qa@example.invalid")
        self.run_git(repository, "remote", "add", "origin", str(remote))
        for path in [
            "quality-loop/skills/quality-qa/SKILL.md",
            "quality-loop/skills/quality-qa/references/reviewer_contract.md",
            "src/product.py", "src/unrelated.txt",
        ]:
            target = repository / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("baseline\n")
        self.run_git(repository, "add", ".")
        self.run_git(repository, "commit", "-m", "baseline")
        self.run_git(repository, "push", "-u", "origin", "master")
        self.run_git(repository, "remote", "set-head", "origin", "master")
        self.run_git(repository, "switch", "-c", "topic/qa")
        (repository / "src/product.py").write_text("reviewed product\n")
        return repository, remote

    def test_prepare_pins_structured_checks_in_invite_and_state(self):
        from qa_workflow.workflow import Workflow

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_git(root, "init", "-b", "main")
            self.run_git(root, "config", "user.name", "QA Test")
            self.run_git(root, "config", "user.email", "qa@example.invalid")
            self.run_git(root, "remote", "add", "origin", "https://github.com/example/repo.git")
            self.run_git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
            for path in [
                "quality-loop/skills/quality-qa/SKILL.md",
                "quality-loop/skills/quality-qa/references/reviewer_contract.md",
                "src/product.py",
            ]:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("pinned fixture\n")
            self.run_git(root, "add", ".")
            self.run_git(root, "commit", "-m", "fixture")
            self.run_git(root, "switch", "-c", "topic/qa")
            check = {"id": "CHECK-PYTEST", "type": "command", "required": True, "argv": ["python", "-m", "pytest", "tests"], "cwd": ".", "env": {"PYTHONDONTWRITEBYTECODE": "1"}, "timeout_seconds": 600, "expected_exit_codes": [0]}
            workflow = Workflow(root)
            result = workflow.prepare(
                "製品動作を確認する", ["期待結果を満たす"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "local", repository="example/repo", checks=[check],
            )
            import json

            state = json.loads((root / result["state_path"]).read_text())
            invite = (root / result["next"]["必要入力"]).read_text()
            self.assertEqual([check], state["checks"])
            self.assertIn("CHECK-PYTEST", invite)
            self.assertIn("Python等の製品検証ツール", invite)
            self.assertIn('"pytest"', invite)
            self.assertIn("quality-loop/skills/quality-qa/references/reviewer_contract.md", invite)
            self.assertNotIn("quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md", invite)
            self.assertIn("日本語Markdown 1ファイル", invite)
            from qa_workflow.store import Store

            Store.validate(state)
            invalid = json.loads(json.dumps(state))
            invalid["revision"] = 0
            with self.assertRaisesRegex(QAError, "revisionまたはサイクル"):
                Store.validate(invalid)
            invalid = json.loads(json.dumps(state))
            invalid["checks"].append(dict(check))
            with self.assertRaisesRegex(QAError, "重複"):
                Store.validate(invalid)
            state_file = root / result["state_path"]
            before = state_file.read_bytes()
            current = workflow.status(prepared_request := result["id"])
            self.assertEqual("prepared", current["phase"])
            self.assertEqual(before, state_file.read_bytes())
            handed = workflow.handoff(prepared_request, revision=current["revision"])
            self.assertEqual("waiting", handed["phase"])
            with self.assertRaisesRegex(QAError, "状態が更新されています"):
                workflow.handoff(prepared_request, revision=current["revision"])

    def test_reqa_cannot_remove_or_weaken_existing_check_contract(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow import gitops
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            repository, _ = self.setup_bare_remote(Path(tmp))
            check = {"id": "CHECK-REQUIRED", "type": "command", "required": True, "argv": ["pytest", "tests"], "cwd": "quality-loop", "env": {"PYTHONDONTWRITEBYTECODE": "1"}, "timeout_seconds": 120, "expected_exit_codes": [0]}
            workflow = Workflow(repository)
            prepared = workflow.prepare("QAを行う", ["基準を満たす"], ["src/product.py"], "Implementer", "Codex (GPT-6)", "local", repository="example/repo", checks=[check])
            self.run_git(repository, "add", "src/product.py")
            self.run_git(repository, "commit", "-m", "reviewed target")
            workflow.finalize(prepared["id"], target="HEAD")
            state = workflow.store.read(prepared["state_path"])
            state["phase"] = "submitted"
            review_hash = "a" * 64
            state["reviews"] = [{"hash": review_hash, "path": state["review_path"], "issues": [], "content_checked": True, "parsed": {"findings": [], "previous": {}}}]
            state["active_review"] = review_hash
            product_paths = ["src/product.py"]
            snapshot = gitops.snapshot(repository, product_paths)
            state["submission"] = {"product_paths": product_paths, "product_snapshot": snapshot}
            workflow.store.save(state, state["revision"], "submitted fixture")
            with self.assertRaisesRegex(QAError, "既存の必須check"):
                workflow.requa(prepared["id"], "local", checks=[])
            weakened = [{**check, "required": False}]
            with self.assertRaisesRegex(QAError, "既存の必須check"):
                workflow.requa(prepared["id"], "local", checks=weakened)
            extra = {"id": "CHECK-EXTRA", "type": "command", "required": False, "argv": ["python", "-m", "compileall", "src"], "cwd": ".", "env": {}, "timeout_seconds": 30, "expected_exit_codes": [0]}
            with self.assertRaisesRegex(QAError, "check契約が変わっています"):
                workflow.requa(prepared["id"], "local", checks=[check, extra])
            with self.assertRaisesRegex(QAError, "必須checkが削除または変更"):
                workflow.requa(
                    prepared["id"], "local", checks=[{**check, "required": False}, extra],
                    check_contract_approval="check契約を変更する",
                )
            weaker_required_checks = [
                {**check, "id": "CHECK-REPLACED"},
                {**check, "argv": ["pytest"]},
                {**check, "cwd": "."},
                {**check, "env": {}},
                {**check, "timeout_seconds": 3600},
                {**check, "expected_exit_codes": [0, 1]},
            ]
            for weaker in weaker_required_checks:
                with self.subTest(weaker=weaker):
                    with self.assertRaisesRegex(QAError, "必須checkが削除または変更"):
                        workflow.requa(
                            prepared["id"], "local", checks=[weaker],
                            check_contract_approval="必須check契約を変更する",
                        )
            from qa_workflow.store import fingerprint
            old_hash = fingerprint([check])
            new_hash = fingerprint([check, extra])
            with self.assertRaisesRegex(QAError, "check契約が変わっています") as caught:
                workflow.requa(
                    prepared["id"], "local", checks=[check, extra],
                    check_contract_approval=f"必須check契約を変更し、旧hash={old_hash} 新hash={'0' * 64}",
                )
            self.assertIn(new_hash, caught.exception.action)
            next_cycle = workflow.requa(
                prepared["id"], "local", checks=[check, extra],
                check_contract_approval=f"必須check契約を変更し、CHECK-EXTRAを追加する。旧hash={old_hash} 新hash={new_hash}",
            )
            next_state = workflow.store.read(next_cycle["state_path"])
            self.assertEqual([check, extra], next_state["checks"])
            self.assertEqual(check, next_state["check_contract_approval"]["previous"][0])
            self.assertEqual(old_hash, next_state["check_contract_approval"]["previous_hash"])
            self.assertEqual(new_hash, next_state["check_contract_approval"]["approved_hash"])
            self.assertEqual(["CHECK-EXTRA"], next_state["check_contract_approval"]["diff"]["added"])

    def test_local_finalize_commits_only_approved_target_and_preserves_other_staged_changes(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow import gitops

        with tempfile.TemporaryDirectory() as tmp:
            repository, _ = self.setup_bare_remote(Path(tmp))
            (repository / "src/unrelated.txt").write_text("unrelated staged edit\n")
            self.run_git(repository, "add", "src/unrelated.txt")
            workflow = Workflow(repository)
            prepared = workflow.prepare(
                "製品変更を固定する", ["対象だけをcommitする"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "local", repository="example/repo",
            )
            result = workflow.finalize(
                prepared["id"], approval="src/product.pyだけcommitしてよい",
                approved_paths=["src/product.py"], revision=prepared["revision"],
            )
            state = workflow.store.read(result["state_path"])
            self.assertEqual("prepared", result["phase"])
            self.assertEqual({"src/product.py"}, gitops.changed(repository, state["baseline"], state["reviewed"]))
            self.assertEqual(["src/unrelated.txt"], gitops.git(repository, "diff", "--cached", "--name-only").splitlines())
            self.assertEqual("unrelated staged edit\n", (repository / "src/unrelated.txt").read_text())

    def test_status_is_read_only_and_requires_selection_when_multiple_requests_are_open(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            repository, _ = self.setup_bare_remote(Path(tmp))
            workflow = Workflow(repository)
            first = workflow.prepare(
                "最初のQA", ["基準を満たす"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "local", repository="example/repo",
            )
            self.run_git(repository, "add", "src/product.py")
            self.run_git(repository, "commit", "-m", "reviewed product")
            workflow.finalize(first["id"], target="HEAD")
            second = workflow.prepare(
                "別のQA", ["別の基準を満たす"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "local", repository="example/repo",
            )
            before = {p.relative_to(repository).as_posix(): p.read_bytes() for p in repository.rglob("*") if p.is_file() and ".git" not in p.parts}
            with self.assertRaisesRegex(QAError, "依頼を一つ選んでください") as error:
                workflow.status()
            self.assertIn(first["id"], str(error.exception))
            self.assertIn(second["id"], str(error.exception))
            selected = workflow.status(first["id"])
            self.assertEqual("prepared", selected["phase"])
            after = {p.relative_to(repository).as_posix(): p.read_bytes() for p in repository.rglob("*") if p.is_file() and ".git" not in p.parts}
            self.assertEqual(before, after)

    def test_status_phase_matrix_provides_next_action_and_rejects_invalid_handoffs(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            repository, _ = self.setup_bare_remote(Path(tmp))
            workflow = Workflow(repository)
            prepared = workflow.prepare(
                "状態遷移を案内する", ["各phaseに次操作がある"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "local", repository="example/repo",
            )
            base = workflow.store.read(prepared["state_path"])
            variants = {}
            draft = json.loads(json.dumps(base)); draft["phase"] = "draft"; draft["reviewed"] = None
            variants["draft"] = draft
            variants["prepared"] = json.loads(json.dumps(base))
            waiting = json.loads(json.dumps(base)); waiting["phase"] = "waiting"
            variants["waiting"] = waiting
            invalid = json.loads(json.dumps(base)); invalid["phase"] = "invalid"
            invalid["pending_correction"] = {"invite": base["invite"], "review_path": base["review_path"]}
            variants["invalid"] = invalid
            planned = json.loads(json.dumps(base)); planned["phase"] = "planned"; planned["plan"] = {"path": base["invite"], "hash": "a" * 64, "paths": ["src/product.py"]}
            variants["planned"] = planned
            approved = json.loads(json.dumps(planned)); approved["phase"] = "approved"
            variants["approved"] = approved
            submitted = json.loads(json.dumps(base)); submitted["phase"] = "submitted"
            variants["submitted"] = submitted
            decision = json.loads(json.dumps(base)); decision["phase"] = "decision"; decision["decision"] = {"path": base["invite"]}
            variants["decision"] = decision
            reviewed = json.loads(json.dumps(base)); reviewed["phase"] = "reviewed"
            reviewed["active_review"] = "b" * 64
            reviewed["reviews"] = [{"hash": "b" * 64, "content_checked": True, "issues": [], "path": base["review_path"], "parsed": {"gate": "PASS", "required_checks": "完了"}}]
            variants["reviewed"] = reviewed
            for phase, state in variants.items():
                with self.subTest(phase=phase):
                    next_step = workflow.describe(state)["next"]
                    self.assertTrue(next_step["担当"])
                    self.assertTrue(next_step["操作"])
                    self.assertTrue(next_step["理由"])
                    self.assertTrue(next_step["必要入力"])
            with self.assertRaisesRegex(QAError, "対象未確定"):
                workflow.handoff(prepared["id"])
            persisted = workflow.store.read(prepared["state_path"])
            persisted["phase"] = "invalid"
            persisted["pending_correction"] = {"invite": persisted["invite"], "review_path": persisted["review_path"]}
            workflow.store.save(persisted, persisted["revision"], "訂正待ちfixture")
            current = workflow.store.read(prepared["state_path"])
            with self.assertRaisesRegex(QAError, "訂正待ち"):
                workflow.plan(prepared["id"], [{"id": "QA-F01"}], current["revision"])
            with self.assertRaisesRegex(QAError, "訂正待ち"):
                workflow.decide(prepared["id"], "終了", "残余なし", current["revision"])

    def test_local_qa_happy_path_records_review_and_separate_user_end_decision(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow import review

        with tempfile.TemporaryDirectory() as tmp:
            repository, _ = self.setup_bare_remote(Path(tmp))
            workflow = Workflow(repository)
            prepared = workflow.prepare(
                "対象製品を確認する", ["期待する動作を満たす"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "local", repository="example/repo",
            )
            self.run_git(repository, "add", "src/product.py")
            self.run_git(repository, "commit", "-m", "reviewed product")
            workflow.finalize(prepared["id"], target="HEAD")
            state = workflow.store.read(prepared["state_path"])
            text = review.template(state, author="Codex (GPT-6)")
            text = text.replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer B")
            text = text.replace("- 結論: INCONCLUSIVE", "- 結論: PASS")
            text = text.replace("- 必須確認: 未完了", "- 必須確認: 完了")
            text = text.replace("- AC-001: 期待する動作を満たす | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載", "- AC-001: 期待する動作を満たす | 判定: PASS | 根拠: src/product.py:1 を確認")
            body = repository / "review.md"
            body.write_text(text)
            acquired = workflow.acquire(prepared["id"], body=body)
            self.assertEqual("content_pending", acquired["phase"])
            first_revision = workflow.store.read(prepared["state_path"])
            source = first_revision["reviews"][0]["sources"][0]
            duplicate = workflow.ingest(prepared["id"], body.read_bytes(), source, acquired["revision"])
            self.assertEqual("content_pending", duplicate["phase"])
            self.assertEqual(1, len(workflow.store.read(prepared["state_path"])["reviews"]))
            reviewed = workflow.confirm_content(prepared["id"], "対象SHAと全受入基準を照合した", "Owner")
            self.assertEqual("reviewed", reviewed["phase"])
            decided = workflow.decide(prepared["id"], "QAを完了として受け入れる", "残余事項なし")
            self.assertEqual("decision", decided["phase"])
            record = (repository / decided["next"]["必要入力"]).read_text()
            self.assertIn("merge・push・外部配置・旧版削除は行いません", record)

    def test_complete_local_cycle_keeps_original_criteria_and_rechecks_previous_finding(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow import review, gitops

        with tempfile.TemporaryDirectory() as tmp:
            repository, _ = self.setup_bare_remote(Path(tmp))
            workflow = Workflow(repository)
            prepared = workflow.prepare(
                "製品の入力検証を保証する", ["空入力を拒否し、理由を返す"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "local", repository="example/repo",
            )
            self.run_git(repository, "add", "src/product.py")
            self.run_git(repository, "commit", "-m", "reviewed initial product")
            workflow.finalize(prepared["id"], target="HEAD")
            first = workflow.store.read(prepared["state_path"])
            text = review.template(first, author="Codex (GPT-6)").replace(
                "- 担当: 別のレビュー担当名", "- 担当: Reviewer B"
            ).replace("- 結論: INCONCLUSIVE", "- 結論: FAIL").replace(
                "- 必須確認: 未完了", "- 必須確認: 完了"
            ).replace(
                "- AC-001: 空入力を拒否し、理由を返す | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
                "- AC-001: 空入力を拒否し、理由を返す | 判定: FAIL | 根拠: src/product.py:1 空入力を受理する",
            )
            finding = "\n### 指摘 QA-F01\n" + "\n".join([
                "- 種別: 要求未達", "- 重大度: 重大", "- 状態: OPEN",
                "- 要求対応: 空入力を拒否する", "- 根拠: src/product.py:1 空入力を再現",
                "- 影響: 不正入力が後続処理へ進む", "- 対応案: 入力境界で拒否する",
                "- 対象: src/product.py", "- 完了条件: 空入力を拒否し理由を返す",
                "- 検証方法: 空入力fixtureを実行する",
            ]) + "\n"
            text = text.replace("\n## 実施側タスク\n", finding + "\n## 実施側タスク\n").replace(
                "修正や追加確認が必要なFindingごとに、細分化した実施タスクを追加し、Finding IDで結び付けてください。不要な場合は「なし」。",
                "- T-01: Finding=QA-F01; path=src/product.py; action=空入力拒否を追加; done_when=理由付き拒否; verify=空入力fixture",
            )
            first_body = repository / "review-first.md"
            first_body.write_text(text)
            workflow.acquire(prepared["id"], body=first_body)
            workflow.confirm_content(prepared["id"], "対象SHAと受入基準を照合した", "Owner")
            planned = workflow.plan(prepared["id"], [{
                "id": "QA-F01", "理解": "空入力が受理される", "方針": "入力境界で検証",
                "対象": ["src/product.py"], "影響": "入力処理",
                "完了条件": "空入力に理由付きエラー", "確認方法": "fixtureで空入力を送る",
            }])
            record_user_prompt(repository, "この計画で修正して")
            workflow.approve(prepared["id"], "この計画で修正して", planned["plan_hash"], ["src/product.py"])
            (repository / "src/product.py").write_text("reject empty input with reason\n")
            workflow.submit(prepared["id"], ["src/product.py"], "空入力fixture成功", [], "QA-F01: 入力境界で検証")
            self.run_git(repository, "add", "src/product.py")
            self.run_git(repository, "commit", "-m", "fix QA-F01")
            requa = workflow.requa(prepared["id"], "local")
            self.assertEqual("QA-F01", next(iter(workflow.store.read(requa["state_path"])["unresolved"])))
            workflow.finalize(requa["id"], target="HEAD")
            second = workflow.store.read(requa["state_path"])
            self.assertEqual(first["initial_baseline"], second["initial_baseline"])
            self.assertEqual(first["reviewed"], second["baseline"])
            self.assertEqual(first["criteria"], second["criteria"])
            text = review.template(second, author="Codex (GPT-6)").replace(
                "- 担当: 別のレビュー担当名", "- 担当: Reviewer B"
            ).replace("- 結論: INCONCLUSIVE", "- 結論: PASS").replace(
                "- 必須確認: 未完了", "- 必須確認: 完了"
            ).replace(
                "- AC-001: 空入力を拒否し、理由を返す | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載",
                "- AC-001: 空入力を拒否し、理由を返す | 判定: PASS | 根拠: src/product.py:1 空入力fixture成功",
            ).replace(
                "- QA-F01: 未検証 | 対象版の根拠と確認方法を記載",
                "- QA-F01: 解消 | 対象SHAのsrc/product.pyを確認し空入力fixture成功",
            )
            second_body = repository / "review-second.md"
            second_body.write_text(text)
            workflow.acquire(requa["id"], body=second_body)
            result = workflow.confirm_content(requa["id"], "修正後の対象SHAでFindingを再確認した", "Owner")
            self.assertEqual({}, workflow.store.read(requa["state_path"])["unresolved"])
            self.assertEqual("reviewed", result["phase"])
            head_before_decision = gitops.sha(repository, "HEAD")
            remote_master_before = subprocess.run(["git", "--git-dir", str(repository.parent / "remote.git"), "rev-parse", "refs/heads/master"], check=True, capture_output=True, text=True).stdout.strip()
            assessed = workflow.assess_residual(requa["id"], "残余事項を受け入れ判断として保留する", "追加の周辺検証は今回の合意範囲外")
            self.assertEqual("reviewed", assessed["phase"])
            assessed_state = workflow.store.read(requa["state_path"])
            self.assertIn("独立QAの実行証明ではありません", (repository / assessed_state["residual_assessment"]["path"]).read_text())
            decision = workflow.decide(requa["id"], "QAを終了して受け入れる", "未検証事項なし")
            self.assertEqual("decision", decision["phase"])
            self.assertEqual(head_before_decision, gitops.sha(repository, "HEAD"))
            remote_master_after = subprocess.run(["git", "--git-dir", str(repository.parent / "remote.git"), "rev-parse", "refs/heads/master"], check=True, capture_output=True, text=True).stdout.strip()
            self.assertEqual(remote_master_before, remote_master_after)

    def test_duplicate_invalid_review_is_revalidated_without_changing_original_body(self):
        from unittest.mock import patch
        from qa_workflow.workflow import Workflow
        from qa_workflow import review

        with tempfile.TemporaryDirectory() as tmp:
            repository, _ = self.setup_bare_remote(Path(tmp))
            workflow = Workflow(repository)
            prepared = workflow.prepare("対象を確認する", ["出力を確認する"], ["src/product.py"], "Implementer", "Codex (GPT-6)", "local", repository="example/repo")
            self.run_git(repository, "add", "src/product.py")
            self.run_git(repository, "commit", "-m", "fix reviewed target")
            workflow.finalize(prepared["id"], target="HEAD")
            state = workflow.store.read(prepared["state_path"])
            body = repository / "review.md"
            raw = review.template(state, author="Reviewer (GPT-6)").replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer B")
            body.write_text(raw)
            with patch("qa_workflow.workflow.review.check", return_value=({}, ["旧validatorのGate矛盾"] )):
                first = workflow.acquire(prepared["id"], body=body)
            self.assertEqual("invalid", first["phase"])
            original = (repository / state["review_path"]).read_bytes()
            second = workflow.acquire(prepared["id"], body=body)
            updated = workflow.store.read(prepared["state_path"])
            self.assertEqual("content_pending", second["phase"])
            self.assertEqual(original, (repository / state["review_path"]).read_bytes())
            self.assertEqual(["旧validatorのGate矛盾"], updated["reviews"][0]["validation_history"][0]["issues"])
            self.assertEqual([], updated["reviews"][0]["issues"])

    def test_legacy_four_file_import_is_read_only_and_checks_gate_consistency(self):
        from qa_workflow.legacy import read_legacy

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "cycle"
            output.mkdir()
            invite = root / "invite.md"
            invite.write_text("## 目的\n旧結果を確認する\n\n## 受入基準\n基準を満たす\n\n- topic: sample\n- cycle: 1\n- baseline: " + "a" * 40 + "\n- reviewed: " + "b" * 40 + "\n")
            machine = {"schema": "blind-qa-cycle-v1", "topic": "sample", "cycle": 1, "baseline": "a" * 40, "reviewed": "b" * 40, "gate": "PASS", "findings": [], "tasks": []}
            (output / "01_review.md").write_text("- topic: sample\n- cycle: 1\n- baseline: " + "a" * 40 + "\n- reviewed: " + "b" * 40 + "\n- gate: PASS\n")
            (output / "02_tasks.md").write_text("# 実施タスク\nなし\n")
            (output / "03_machine.json").write_text(json.dumps(machine))
            (output / "STATUS.md").write_text("PASS\n")
            paths = [invite, *output.iterdir()]
            before = {path.name: path.read_bytes() for path in paths}
            accepted = read_legacy(output, invite)
            self.assertTrue(accepted["valid"], accepted["issues"])
            invite.write_text("## 目的\n旧結果を確認する\n\n- topic: sample\n- cycle: 1\n- baseline: " + "a" * 40 + "\n- reviewed: " + "b" * 40 + "\n")
            missing_requirements = read_legacy(output, invite)
            self.assertFalse(missing_requirements["valid"])
            self.assertTrue(any("目的・受入基準" in issue for issue in missing_requirements["issues"]))
            invite.write_bytes(before["invite.md"])
            machine["tasks"] = [{"id": "T-01", "closes": "QA-F404", "verify": "pytest"}]
            (output / "03_machine.json").write_text(json.dumps(machine))
            (output / "02_tasks.md").write_text("# 実施タスク\nT-01\n")
            unknown = read_legacy(output, invite)
            self.assertFalse(unknown["valid"])
            self.assertTrue(any("未知指摘" in issue for issue in unknown["issues"]), unknown["issues"])
            machine["tasks"] = []
            (output / "03_machine.json").write_text(json.dumps(machine))
            (output / "STATUS.md").write_text("HOLD\n")
            rejected = read_legacy(output, invite)
            self.assertFalse(rejected["valid"])
            self.assertIn("STATUSと機械JSONのGateが不一致", rejected["issues"])
            self.assertEqual(before["invite.md"], invite.read_bytes())
            self.assertEqual(json.dumps(machine), (output / "03_machine.json").read_text())

    def test_submitted_snapshot_blocks_later_change_to_other_product(self):
        from qa_workflow.workflow import Workflow
        import json

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_git(root, "init", "-b", "main")
            self.run_git(root, "config", "user.name", "QA Test")
            self.run_git(root, "config", "user.email", "qa@example.invalid")
            self.run_git(root, "remote", "add", "origin", "https://github.com/example/repo.git")
            self.run_git(root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
            for path in [
                "quality-loop/skills/quality-qa/SKILL.md",
                "quality-loop/skills/quality-qa/references/reviewer_contract.md",
                "src/product-a.py", "src/product-b.py",
            ]:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("baseline\n")
            self.run_git(root, "add", ".")
            self.run_git(root, "commit", "-m", "fixture")
            self.run_git(root, "switch", "-c", "topic/qa")
            workflow = Workflow(root)
            prepared = workflow.prepare(
                "製品の受入確認", ["不具合を検出できる"], ["src/product-a.py", "src/product-b.py"],
                "Implementer", "Codex (GPT-6)", "local", repository="example/repo",
            )
            state = json.loads((root / prepared["state_path"]).read_text())
            text = review.template(state, author="Codex (GPT-6)").replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer B")
            text = text.replace("- 結論: INCONCLUSIVE", "- 結論: FAIL").replace("- 必須確認: 未完了", "- 必須確認: 完了")
            text = text.replace("- AC-001: 不具合を検出できる | 判定: UNVERIFIED | 根拠: 対象版の根拠と確認結果を記載", "- AC-001: 不具合を検出できる | 判定: PASS | 根拠: src/product-a.py:1 確認済み")
            finding = "\n### 指摘 QA-F02\n- 種別: 不具合\n- 重大度: 通常\n- 状態: OPEN\n- 要求対応: 提出後snapshotを保護する\n- 根拠: src/product-a.py:1 境界で再現\n- 影響: 未承認pathの混入\n- 対応案: 提出path全体のsnapshotを固定する\n- 対象: src/product-a.py\n- 完了条件: 別pathの提出後変更を拒否する\n- 検証方法: 複数製品fixtureで再QAを拒否する\n"
            text = text.replace("\n## 実施側タスク\n", finding + "\n## 実施側タスク\n")
            text = text.replace("修正や追加確認が必要なFindingごとに、細分化した実施タスクを追加し、Finding IDで結び付けてください。不要な場合は「なし」。", "- T-01: Finding=QA-F02; path=src/product-a.py; action=提出時snapshotを検証; done_when=別path変更を拒否; verify=fixtureで再QAを試す")
            review_file = root / "review.md"
            review_file.write_text(text)
            product_before_plan = (root / "src/product-a.py").read_bytes()
            acquired = workflow.acquire(prepared["id"], body=review_file)
            confirmed = workflow.confirm_content(prepared["id"], "対象SHAと受入基準、Finding根拠を確認した", "Reviewer B")
            planned = workflow.plan(prepared["id"], [{"id": "QA-F02", "理解": "提出後の製品集合を固定する", "方針": "全製品pathのsnapshotを照合", "対象": ["src/product-a.py"], "影響": "再QA対象の完全性", "完了条件": "他path変更を拒否", "確認方法": "複数path fixture"}])
            self.assertEqual(product_before_plan, (root / "src/product-a.py").read_bytes())
            with self.assertRaisesRegex(QAError, "修正承認がありません"):
                workflow.submit(prepared["id"], ["src/product-a.py"], "検証した", [])
            record_user_prompt(root, "この計画で修正して")
            with self.assertRaisesRegex(QAError, "計画・対象・レビューが承認時点と一致"):
                workflow.approve(prepared["id"], "この計画で修正して", "0" * 64, ["src/product-a.py"])
            approved = workflow.approve(prepared["id"], "この計画で修正して", planned["plan_hash"], ["src/product-a.py"])
            with self.assertRaisesRegex(QAError, "実装方式が変わっています"):
                workflow.submit(prepared["id"], ["src/product-a.py"], "回帰確認", [], "QA-F02: 別方式")
            (root / "src/product-a.py").write_text("approved fix\n")
            submitted = workflow.submit(prepared["id"], ["src/product-a.py"], "pytestで回帰確認", [], "QA-F02: 全製品pathのsnapshotを照合")
            requa = workflow.requa(prepared["id"], "local")
            requa_state = workflow.store.read(requa["state_path"])
            self.assertEqual("draft", requa["phase"])
            self.assertEqual(prepared["reviewed"], requa_state["baseline"])
            self.assertEqual(["不具合を検出できる"], requa_state["criteria"])
            self.assertEqual("QA-F02", next(iter(requa_state["unresolved"])))
            (root / "src/product-b.py").write_text("unapproved later change\n")
            with self.assertRaisesRegex(QAError, "修正提出後に製品対象が変更"):
                workflow.requa(prepared["id"], "local")
            self.assertEqual("submitted", submitted["phase"])

    def test_cloud_publish_creates_only_approved_target_and_invite_commits(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow import gitops

        with tempfile.TemporaryDirectory() as tmp:
            repository, remote = self.setup_bare_remote(Path(tmp))
            (repository / "src/unrelated.txt").write_text("staged user change\n")
            self.run_git(repository, "add", "src/unrelated.txt")
            workflow = Workflow(repository)
            prepared = workflow.prepare(
                "対象製品をQAする", ["対象製品を読むこと"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "cloud", repository="example/repo",
            )
            invite = prepared["next"]["必要入力"]
            published = workflow.publish(
                prepared["id"], "クラウドQAに出して", ["src/product.py", invite],
            )
            state = workflow.store.read(published["state_path"])
            target = gitops.sha(repository, state["reviewed"])
            self.assertEqual("published", published["phase"])
            self.assertTrue(gitops.ancestor(repository, target, state["published"]["tip"]))
            self.assertTrue(gitops.ancestor(repository, state["invite_commit"], state["published"]["tip"]))
            self.assertEqual({"src/product.py"}, gitops.changed(repository, state["baseline"], target))
            self.assertIn(state["invite"], gitops.changed(repository, target, state["invite_commit"]))
            committed_invite = gitops.tree_snapshot(repository, state["invite_commit"], [state["invite"]])[state["invite"]]
            self.assertEqual(state["publication_scan"]["invite_hash"], committed_invite["hash"])
            self.assertEqual(state["invite_commit"], state["publication_scan"]["invite_commit"])
            self.assertEqual(["src/unrelated.txt"], gitops.git(repository, "diff", "--cached", "--name-only").splitlines())
            self.assertNotIn("src/unrelated.txt", gitops.changed(repository, state["baseline"], state["published"]["tip"]))
            remote_tip = gitops.remote_tip(repository, "topic/qa")
            self.assertEqual(state["published"]["tip"], remote_tip)

    def test_publish_rejects_invite_mutation_after_final_scan_before_invite_commit(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow import gitops
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            repository, remote = self.setup_bare_remote(Path(tmp))
            workflow = Workflow(repository)
            prepared = workflow.prepare(
                "対象をQAする", ["最終依頼hashを固定する"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "cloud", repository="example/repo",
            )
            invite = prepared["next"]["必要入力"]
            remote_before = gitops.remote_tip(repository, "topic/qa")
            real_commit_paths = gitops.commit_paths

            def mutate_invite_before_commit(root, paths, expected, message):
                if list(paths) == [invite]:
                    (repository / invite).write_text((repository / invite).read_text() + "\nlate mutation\n")
                return real_commit_paths(root, paths, expected, message)

            gitops.commit_paths = mutate_invite_before_commit
            try:
                with self.assertRaisesRegex(QAError, "表示済み対象から内容が変わりました"):
                    workflow.publish(prepared["id"], "クラウドQAに出して", ["src/product.py", invite])
            finally:
                gitops.commit_paths = real_commit_paths
            state = workflow.store.read(prepared["state_path"])
            self.assertEqual(remote_before, gitops.remote_tip(repository, "topic/qa"))
            self.assertIsNone(state["published"])
            self.assertNotIn("invite_commit", state)

    def test_cloud_publish_requires_snapshot_bound_check_evidence_before_any_git_mutation(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow import gitops
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            repository, remote = self.setup_bare_remote(Path(tmp))
            check = {"id": "CHECK-SMOKE", "type": "command", "required": True, "argv": ["python3", "-c", "print('ok')"], "cwd": ".", "env": {}, "timeout_seconds": 10, "expected_exit_codes": [0]}
            workflow = Workflow(repository)
            prepared = workflow.prepare("対象を検査する", ["検査が成功する"], ["src/product.py"], "Implementer", "Codex (GPT-6)", "cloud", repository="example/repo", checks=[check])
            invite = prepared["next"]["必要入力"]
            head_before = gitops.sha(repository, "HEAD")
            remote_before = gitops.remote_tip(repository, "topic/qa")
            self.run_git(repository, "add", "src/unrelated.txt")
            index_before = gitops.git(repository, "diff", "--cached", "--name-only")
            with self.assertRaisesRegex(QAError, "必須checkの成功Evidence"):
                workflow.publish(prepared["id"], "クラウドQAに出して", ["src/product.py", invite])
            self.assertEqual(head_before, gitops.sha(repository, "HEAD"))
            self.assertEqual(remote_before, gitops.remote_tip(repository, "topic/qa"))
            self.assertEqual(index_before, gitops.git(repository, "diff", "--cached", "--name-only"))
            verified = workflow.verify(prepared["id"])
            evidence = workflow.store.read(prepared["state_path"])["check_evidence"]
            self.assertEqual("PASS", evidence["results"][0]["status"])
            original = (repository / "src/product.py").read_text()
            (repository / "src/product.py").write_text(original + "changed after verify\n")
            with self.assertRaisesRegex(QAError, "snapshotが依頼固定時点から変化"):
                workflow.publish(prepared["id"], "クラウドQAに出して", ["src/product.py", invite], revision=verified["revision"])
            self.assertEqual(head_before, gitops.sha(repository, "HEAD"))
            (repository / "src/product.py").write_text(original)
            published = workflow.publish(prepared["id"], "クラウドQAに出して", ["src/product.py", invite], revision=verified["revision"])
            self.assertEqual("published", published["phase"])

    def test_publish_secret_and_personal_path_guards_stop_before_commit_or_push(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow import gitops
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            repository, remote = self.setup_bare_remote(Path(tmp))
            (repository / "src/product.py").write_text("\n".join(["API_TOKEN" + "=live-secret-value-123", "path=" + "/" + "Users/real-person/private/data.csv", "-----BEGIN " + "PRIVATE KEY-----"]) + "\n")
            (repository / "src/unrelated.txt").write_text("staged unrelated edit\n")
            self.run_git(repository, "add", "src/unrelated.txt")
            workflow = Workflow(repository)
            prepared = workflow.prepare("対象を公開する", ["対象を確認"], ["src/product.py"], "Implementer", "Codex (GPT-6)", "cloud", repository="example/repo")
            invite = prepared["next"]["必要入力"]
            head_before = gitops.sha(repository, "HEAD")
            index_before = gitops.git(repository, "diff", "--cached", "--name-only")
            remote_before = subprocess.run(["git", "--git-dir", str(remote), "rev-parse", "refs/heads/master"], check=True, capture_output=True, text=True).stdout.strip()
            with self.assertRaisesRegex(QAError, "機密情報または個人ローカルパス") as raised:
                workflow.publish(prepared["id"], "クラウドQAに出して", ["src/product.py", invite])
            self.assertIn("secret-like-assignment", raised.exception.action)
            self.assertIn("personal-local-path", raised.exception.action)
            self.assertIn("private-key", raised.exception.action)
            self.assertEqual(head_before, gitops.sha(repository, "HEAD"))
            self.assertEqual(index_before, gitops.git(repository, "diff", "--cached", "--name-only"))
            self.assertEqual(remote_before, subprocess.run(["git", "--git-dir", str(remote), "rev-parse", "refs/heads/master"], check=True, capture_output=True, text=True).stdout.strip())
            self.assertIsNone(workflow.store.read(prepared["state_path"])["reviewed"])

    def test_final_scan_rejection_persists_target_and_invite_state_without_invite_commit(self):
        from unittest.mock import patch
        from qa_workflow import gitops
        from qa_workflow.store import digest, fingerprint
        from qa_workflow.workflow import Workflow

        for name, injected in [
            ("secret", "API_TOKEN" + "=live-secret-value-123"),
            ("personal-path", "/" + "Users/real-person/private/data.csv"),
        ]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                repository, remote = self.setup_bare_remote(Path(tmp))
                (repository / "src/unrelated.txt").write_text("staged unrelated edit\n")
                self.run_git(repository, "add", "src/unrelated.txt")
                workflow = Workflow(repository)
                prepared = workflow.prepare(
                    "対象製品をQAする", ["対象製品を確認する"], ["src/product.py"],
                    "Implementer", "Codex (GPT-6)", "cloud", repository="example/repo",
                )
                invite = prepared["next"]["必要入力"]
                head_before = gitops.sha(repository, "HEAD")
                index_before = gitops.git(repository, "diff", "--cached", "--name-only")
                remote_before = subprocess.run(
                    ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/master"],
                    check=True, capture_output=True, text=True,
                ).stdout.strip()
                original_invite = review.invite

                def inject_after_target_is_fixed(state):
                    body = original_invite(state)
                    return body + ("\n" + injected + "\n" if state["reviewed"] else "")

                with patch("qa_workflow.workflow.review.invite", side_effect=inject_after_target_is_fixed):
                    with self.assertRaisesRegex(QAError, "最終公開対象") as raised:
                        workflow.publish(prepared["id"], "クラウドQAに出して", ["src/product.py", invite])

                state = workflow.store.read(prepared["state_path"])
                target = gitops.sha(repository, "HEAD")
                final_invite_bytes = (repository / invite).read_bytes()
                self.assertNotEqual(head_before, target)
                self.assertEqual(target, state["reviewed"])
                self.assertEqual(digest(final_invite_bytes), state["invite_hash"])
                self.assertEqual(state["invite_hash"], state["publication_scan"]["invite_hash"])
                self.assertEqual(fingerprint(state["reviewer_materials"]), state["publication_scan"]["reviewer_materials_hash"])
                self.assertEqual(fingerprint(state["checks"]), state["publication_scan"]["check_contract_hash"])
                self.assertEqual(target, state["publication_scan"]["reviewed"])
                self.assertEqual("REJECTED", state["publication_scan"]["scan_result"])
                self.assertEqual("final-publication-scan", state["publication_scan"]["stage"])
                self.assertTrue(state["publication_scan"]["started_at"])
                self.assertTrue(state["publication_scan"]["completed_at"])
                finding = "secret-like-assignment" if name == "secret" else "personal-local-path"
                self.assertTrue(any(item.endswith(finding) for item in state["publication_scan"]["findings"]))
                self.assertNotIn(injected, state["publish_error"])
                self.assertIn("新しいQA依頼/state", raised.exception.action)
                self.assertEqual({"src/product.py"}, gitops.changed(repository, state["baseline"], target))
                self.assertNotIn("invite_commit", state)
                self.assertIsNone(state["published"])
                self.assertEqual(index_before, gitops.git(repository, "diff", "--cached", "--name-only"))
                self.assertEqual(remote_before, subprocess.run(
                    ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/master"],
                    check=True, capture_output=True, text=True,
                ).stdout.strip())

                status = workflow.status(prepared["id"])
                self.assertIsNone(status["next"]["依頼文"])
                self.assertIn("新しいQA依頼/state", status["next"]["操作"])
                with self.assertRaisesRegex(QAError, "拒否済み") as retry:
                    workflow.publish(prepared["id"], "クラウドQAに出して", ["src/product.py", invite])
                self.assertIn("--reviewed " + target, retry.exception.action)
                self.assertEqual(target, gitops.sha(repository, "HEAD"))
                self.assertEqual(index_before, gitops.git(repository, "diff", "--cached", "--name-only"))
                self.assertEqual(remote_before, subprocess.run(
                    ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/master"],
                    check=True, capture_output=True, text=True,
                ).stdout.strip())

                old_state_bytes = (repository / prepared["state_path"]).read_bytes()
                old_invite_bytes = (repository / invite).read_bytes()
                replacement = workflow.prepare(
                    "対象製品をQAする", ["対象製品を確認する"], ["src/product.py"],
                    "Implementer", "Codex (GPT-6)", "cloud", baseline=state["baseline"],
                    reviewed=target, repository="example/repo",
                )
                self.assertNotEqual(prepared["id"], replacement["id"])
                self.assertEqual(target, replacement["reviewed"])
                self.assertEqual(old_state_bytes, (repository / prepared["state_path"]).read_bytes())
                self.assertEqual(old_invite_bytes, (repository / invite).read_bytes())
                self.assertEqual(index_before, gitops.git(repository, "diff", "--cached", "--name-only"))
                self.assertEqual(remote_before, subprocess.run(
                    ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/master"],
                    check=True, capture_output=True, text=True,
                ).stdout.strip())

    def test_publication_scanner_allows_explicit_synthetic_fixture_markers(self):
        from qa_workflow import gitops
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = root / "fixture.md"
            fixture.write_text("\n".join(["API_KEY=test-token", "path=/Users/qa-user/private/data.csv"]) + "\n")
            self.assertEqual([], gitops.publication_findings(root, {"fixture.md"}))

    def test_cloud_publish_on_default_branch_stops_before_git_mutation(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow import gitops
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            repository, remote = self.setup_bare_remote(Path(tmp))
            self.run_git(repository, "restore", "src/product.py")
            self.run_git(repository, "switch", "master")
            workflow = Workflow(repository)
            prepared = workflow.prepare(
                "対象製品をQAする", ["対象製品を読むこと"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "cloud", repository="example/repo",
            )
            before_head = gitops.sha(repository, "HEAD")
            before_remote = subprocess.run(["git", "--git-dir", str(remote), "rev-parse", "refs/heads/master"], check=True, capture_output=True, text=True).stdout.strip()
            invite = prepared["next"]["必要入力"]
            with self.assertRaisesRegex(QAError, "選択された開発ブランチ"):
                workflow.publish(prepared["id"], "クラウドQAに出して", ["src/product.py", invite])
            self.assertEqual(before_head, gitops.sha(repository, "HEAD"))
            after_remote = subprocess.run(["git", "--git-dir", str(remote), "rev-parse", "refs/heads/master"], check=True, capture_output=True, text=True).stdout.strip()
            self.assertEqual(before_remote, after_remote)

    def test_cloud_publish_retry_reuses_commits_after_transient_push_failure(self):
        from unittest.mock import patch
        from qa_workflow.workflow import Workflow
        from qa_workflow import gitops
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            repository, remote = self.setup_bare_remote(Path(tmp))
            workflow = Workflow(repository)
            prepared = workflow.prepare(
                "対象製品をQAする", ["対象製品の動作を確認する"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "cloud", repository="example/repo",
            )
            invite = prepared["next"]["必要入力"]
            real_push = gitops.push
            attempts = []

            def fail_once(root, state, invite_commit):
                attempts.append(invite_commit)
                if len(attempts) == 1:
                    raise QAError("一時的なpush失敗")
                return real_push(root, state, invite_commit)

            with patch("qa_workflow.workflow.gitops.push", side_effect=fail_once):
                with self.assertRaisesRegex(QAError, "一時的なpush失敗") as raised:
                    workflow.publish(prepared["id"], "クラウドQAに出して", ["src/product.py", invite])
                self.assertIn("公開を再試行", raised.exception.action)
                failed = workflow.status(prepared["id"])
                self.assertEqual("prepared", failed["phase"])
                retried = workflow.publish(
                    prepared["id"], "クラウドQAに出して", ["src/product.py", invite],
                    revision=failed["revision"],
                )
            self.assertEqual("published", retried["phase"])
            self.assertEqual(2, len(attempts))
            self.assertEqual(attempts[0], attempts[1])
            state = workflow.store.read(retried["state_path"])
            self.assertEqual(state["published"]["tip"], gitops.remote_tip(repository, "topic/qa"))
            self.assertIn("src/product.py", gitops.changed(repository, state["baseline"], state["reviewed"]))

    def test_cloud_publish_recovers_when_target_commit_was_created_before_interruption(self):
        from unittest.mock import patch
        from qa_workflow.workflow import Workflow
        from qa_workflow import gitops
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            repository, _ = self.setup_bare_remote(Path(tmp))
            workflow = Workflow(repository)
            prepared = workflow.prepare(
                "対象製品をQAする", ["対象製品の動作を確認する"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "cloud", repository="example/repo",
            )
            invite = prepared["next"]["必要入力"]
            real_commit = gitops.commit_paths
            target_commits = []

            def commit_then_interrupt(root, paths, expected, message):
                result = real_commit(root, paths, expected, message)
                if list(paths) == ["src/product.py"] and not target_commits:
                    target_commits.append(result)
                    raise QAError("対象commit直後に中断")
                return result

            with patch("qa_workflow.workflow.gitops.commit_paths", side_effect=commit_then_interrupt):
                with self.assertRaisesRegex(QAError, "対象commit直後"):
                    workflow.publish(prepared["id"], "クラウドQAに出して", ["src/product.py", invite])
            self.assertEqual(target_commits[0], gitops.sha(repository, "HEAD"))
            self.assertIsNone(gitops.remote_tip(repository, "topic/qa"))
            current = workflow.status(prepared["id"])
            retried = workflow.publish(
                prepared["id"], "クラウドQAに出して", ["src/product.py", invite],
                revision=current["revision"],
            )
            state = workflow.store.read(retried["state_path"])
            self.assertEqual(target_commits[0], state["reviewed"])
            self.assertEqual("published", retried["phase"])

    def test_cloud_publish_recovers_when_invite_commit_was_created_before_interruption(self):
        from unittest.mock import patch
        from qa_workflow.workflow import Workflow
        from qa_workflow import gitops
        from qa_workflow.store import QAError

        with tempfile.TemporaryDirectory() as tmp:
            repository, _ = self.setup_bare_remote(Path(tmp))
            workflow = Workflow(repository)
            prepared = workflow.prepare(
                "対象製品をQAする", ["対象製品の動作を確認する"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "cloud", repository="example/repo",
            )
            invite = prepared["next"]["必要入力"]
            real_commit = gitops.commit_paths
            invite_commits = []

            def commit_then_interrupt(root, paths, expected, message):
                result = real_commit(root, paths, expected, message)
                if list(paths) == [invite] and not invite_commits:
                    invite_commits.append(result)
                    raise QAError("依頼commit直後に中断")
                return result

            with patch("qa_workflow.workflow.gitops.commit_paths", side_effect=commit_then_interrupt):
                with self.assertRaisesRegex(QAError, "依頼commit直後"):
                    workflow.publish(prepared["id"], "クラウドQAに出して", ["src/product.py", invite])
            current = workflow.status(prepared["id"])
            retried = workflow.publish(
                prepared["id"], "クラウドQAに出して", ["src/product.py", invite],
                revision=current["revision"],
            )
            state = workflow.store.read(retried["state_path"])
            self.assertEqual(invite_commits[0], state["invite_commit"])
            self.assertTrue(gitops.ancestor(repository, invite_commits[0], state["published"]["tip"]))

    def test_preflight_fast_forwards_only_registered_remote_review_and_rejects_product_ahead(self):
        from qa_workflow import gitops
        from qa_workflow.store import digest, QAError

        with tempfile.TemporaryDirectory() as tmp:
            repository, remote = self.setup_bare_remote(Path(tmp))
            self.run_git(repository, "add", "src/product.py")
            self.run_git(repository, "commit", "-m", "fixed QA target")
            target = gitops.sha(repository, "HEAD")
            self.run_git(repository, "push", "origin", "HEAD:refs/heads/topic/qa")
            writer = Path(tmp) / "writer"
            subprocess.run(["git", "clone", str(remote), str(writer)], check=True, capture_output=True)
            self.run_git(writer, "config", "user.name", "QA Reviewer")
            self.run_git(writer, "config", "user.email", "reviewer@example.invalid")
            self.run_git(writer, "switch", "topic/qa")
            review_path = "docs/Artifacts/qa_review_001_1004.md"
            body = b"# Independent review\n\nEvidence\n"
            local_review = repository / review_path
            local_review.parent.mkdir(parents=True, exist_ok=True)
            local_review.write_bytes(body)
            remote_review = writer / review_path
            remote_review.parent.mkdir(parents=True, exist_ok=True)
            remote_review.write_bytes(body)
            self.run_git(writer, "add", review_path)
            self.run_git(writer, "commit", "-m", "review artifact only")
            self.run_git(writer, "push", "origin", "topic/qa")
            state = {
                "branch": "topic/qa", "review_path": review_path, "reviews": [],
                "history_reviews": [{"path": review_path, "hash": digest(body)}],
                "pending_correction": None,
            }
            flight = gitops.preflight(repository, state, {"src/product.py", review_path})
            self.assertEqual(gitops.remote_tip(repository, "topic/qa"), gitops.sha(repository, "HEAD"))
            self.assertEqual(body, local_review.read_bytes())
            self.assertEqual([], flight["commits"])

            (writer / "src/product.py").write_text("unapproved remote product change\n")
            self.run_git(writer, "add", "src/product.py")
            self.run_git(writer, "commit", "-m", "unapproved product change")
            self.run_git(writer, "push", "origin", "topic/qa")
            before = gitops.sha(repository, "HEAD")
            with self.assertRaisesRegex(QAError, "remote先行分"):
                gitops.preflight(repository, state, {"src/product.py", review_path})
            self.assertEqual(before, gitops.sha(repository, "HEAD"))

    def test_invalid_review_is_preserved_and_old_path_cannot_replace_reserved_correction(self):
        from qa_workflow.workflow import Workflow
        from qa_workflow.store import QAError, digest

        with tempfile.TemporaryDirectory() as tmp:
            repository, _ = self.setup_bare_remote(Path(tmp))
            workflow = Workflow(repository)
            prepared = workflow.prepare(
                "対象製品をQAする", ["対象製品を読むこと"], ["src/product.py"],
                "Implementer", "Codex (GPT-6)", "local", repository="example/repo",
            )
            self.run_git(repository, "add", "src/product.py")
            self.run_git(repository, "commit", "-m", "reviewed product")
            workflow.finalize(prepared["id"], target="HEAD")
            original = repository / "incomplete.md"
            original.write_text("# broken\n")
            invalid = workflow.acquire(prepared["id"], body=original)
            self.assertEqual("invalid", invalid["phase"])
            state = workflow.store.read(prepared["state_path"])
            old_path = state["review_path"]
            old_bytes = (repository / old_path).read_bytes()
            old_hash = digest(old_bytes)
            source = state["reviews"][0]["sources"][0]
            with self.assertRaisesRegex(QAError, "同名別内容"):
                workflow.ingest(prepared["id"], b"different body at reserved path", source, invalid["revision"])
            symlink = repository / "review-link.md"
            symlink.symlink_to(original)
            with self.assertRaisesRegex(QAError, "通常ファイル"):
                workflow.acquire(prepared["id"], body=symlink, revision=workflow.store.read(prepared["state_path"])["revision"])
            correction = workflow.correction(prepared["id"], "必須契約項目が不足しています")
            updated = workflow.store.read(prepared["state_path"])
            new_path = updated["pending_correction"]["review_path"]
            self.assertNotEqual(old_path, new_path)
            with self.assertRaisesRegex(QAError, "予約された返却パス"):
                workflow.ingest(prepared["id"], b"replacement", {"kind": "body", "commit": None, "path": old_path}, correction["revision"])
            self.assertEqual(old_hash, digest((repository / old_path).read_bytes()))
            self.assertFalse((repository / new_path).exists())
            corrected_text = review.template(updated, author="Codex (GPT-6)", expected=updated["pending_correction"])
            corrected_text = corrected_text.replace("- 担当: 別のレビュー担当名", "- 担当: Reviewer C")
            corrected = repository / "corrected.md"
            corrected.write_text(corrected_text)
            received = workflow.acquire(prepared["id"], body=corrected, revision=updated["revision"])
            self.assertEqual("content_pending", received["phase"])
            self.assertEqual(old_hash, digest((repository / old_path).read_bytes()))
            accepted = workflow.confirm_content(prepared["id"], "訂正版の対象・基準を照合した", "Owner")
            self.assertEqual("reviewed", accepted["phase"])


if __name__ == "__main__":
    unittest.main()
