from __future__ import annotations

import subprocess
import tempfile
import unittest
import base64
import json
from pathlib import Path

from qa_workflow import review
from qa_workflow.store import QAError
from qa_workflow.workflow import verify_submission_snapshot


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
            {"path": "quality-loop/skills/blind-qa-cycle/SKILL.md", "sha256": "c" * 64},
            {
                "path": "quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md",
                "sha256": "d" * 64,
            },
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
            "quality-loop/skills/blind-qa-cycle/SKILL.md",
            "quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md",
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
                "quality-loop/skills/blind-qa-cycle/SKILL.md",
                "quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md",
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
            reviewed = workflow.confirm_content(prepared["id"], "対象SHAと全受入基準を照合した", "Owner")
            self.assertEqual("reviewed", reviewed["phase"])
            decided = workflow.decide(prepared["id"], "QAを完了として受け入れる", "残余事項なし")
            self.assertEqual("decision", decided["phase"])
            record = (repository / decided["next"]["必要入力"]).read_text()
            self.assertIn("merge・push・外部配置・旧版削除は行いません", record)

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
                "quality-loop/skills/blind-qa-cycle/SKILL.md",
                "quality-loop/skills/blind-qa-cycle/references/cloud_output_contract.md",
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
            with self.assertRaisesRegex(QAError, "計画・対象・レビューが承認時点と一致"):
                workflow.approve(prepared["id"], "この計画で修正して", "0" * 64, ["src/product-a.py"])
            approved = workflow.approve(prepared["id"], "この計画で修正して", planned["plan_hash"], ["src/product-a.py"])
            (root / "src/product-a.py").write_text("approved fix\n")
            submitted = workflow.submit(prepared["id"], ["src/product-a.py"], "pytestで回帰確認", [])
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
            self.assertEqual(["src/unrelated.txt"], gitops.git(repository, "diff", "--cached", "--name-only").splitlines())
            self.assertNotIn("src/unrelated.txt", gitops.changed(repository, state["baseline"], state["published"]["tip"]))
            remote_tip = gitops.remote_tip(repository, "topic/qa")
            self.assertEqual(state["published"]["tip"], remote_tip)

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
