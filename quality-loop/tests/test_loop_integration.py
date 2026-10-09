from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from qa_workflow import gitops, review
from qa_workflow.repair_commit import COMMIT_PHRASE
from qa_workflow.store import QAError
from qa_workflow.workflow import Workflow

CLOUD = "クラウドQAに出して"
APPROVAL = f"この計画で修正して。{COMMIT_PHRASE}。{CLOUD}"


def record_user_prompt(repository: Path, prompt: str) -> None:
    with (repository / ".git" / "qa-user-prompts.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({"prompt": prompt}, ensure_ascii=False) + "\n")


def run_git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


def setup_bare_remote(root: Path) -> tuple[Path, Path]:
    repository = root / "repo"
    remote = root / "remote.git"
    subprocess.run(["git", "init", "--bare", "-b", "master", str(remote)], check=True, capture_output=True)
    repository.mkdir()
    run_git(repository, "init", "-b", "master")
    run_git(repository, "config", "user.name", "QA Test")
    run_git(repository, "config", "user.email", "qa@example.invalid")
    run_git(repository, "remote", "add", "origin", str(remote))
    for path in [
        "quality-loop/skills/quality-qa/SKILL.md",
        "quality-loop/skills/quality-qa/references/reviewer_contract.md",
        "src/product.py",
    ]:
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("baseline\n")
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", "baseline")
    run_git(repository, "push", "-u", "origin", "master")
    run_git(repository, "remote", "set-head", "origin", "master")
    run_git(repository, "switch", "-c", "topic/qa")
    return repository, remote


def failed_review(state: dict) -> str:
    text = review.template(state, author="Codex (GPT-6)").replace(
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
    return text.replace("\n## 実施側タスク\n", finding + "\n## 実施側タスク\n").replace(
        "修正や追加確認が必要なFindingごとに、細分化した実施タスクを追加し、Finding IDで結び付けてください。不要な場合は「なし」。",
        "- T-01: Finding=QA-F01; path=src/product.py; action=空入力拒否を追加; done_when=理由付き拒否; verify=空入力fixture",
    )


class LoopIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.repository, self.remote = setup_bare_remote(Path(self.directory.name))
        self.workflow = Workflow(self.repository)
        (self.repository / "src/product.py").write_text("accept any input\n")
        prepared = self.workflow.prepare(
            "製品の入力検証を保証する", ["空入力を拒否し、理由を返す"], ["src/product.py"],
            "Implementer", "Codex (GPT-6)", "local", repository="example/repo",
        )
        self.prepared = prepared
        run_git(self.repository, "add", "src/product.py")
        run_git(self.repository, "commit", "-m", "reviewed initial product")
        self.workflow.finalize(prepared["id"], target="HEAD")
        state = self.workflow.store.read(prepared["state_path"])
        body = self.repository / "review-first.md"
        body.write_text(failed_review(state))
        self.workflow.acquire(prepared["id"], body=body)
        self.workflow.confirm_content(prepared["id"], "対象SHAと受入基準を照合した", "Owner")
        self.planned = self.workflow.plan(prepared["id"], [{
            "id": "QA-F01", "理解": "空入力が受理される", "方針": "入力境界で検証",
            "対象": ["src/product.py"], "影響": "入力処理",
            "完了条件": "空入力に理由付きエラー", "確認方法": "fixtureで空入力を送る",
        }])

    def tearDown(self):
        self.directory.cleanup()

    def approve(self, message: str) -> None:
        record_user_prompt(self.repository, message)
        self.workflow.approve(self.prepared["id"], message, self.planned["plan_hash"], ["src/product.py"])

    def fix_product(self) -> None:
        (self.repository / "src/product.py").write_text("reject empty input with reason\n")

    def test_loop_before_approval_runs_nothing(self):
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("waiting_approval", result["status"])
        self.assertEqual(1, len(self.workflow.store.states()))

    def test_approved_loop_commits_submits_and_publishes_re_qa_request(self):
        self.approve(APPROVAL)
        self.fix_product()
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("completed", result["status"], result)
        self.assertEqual(["commit", "submit", "push", "ancestry", "requa-request", "finalize", "publish"], result["completed"])
        states = {state["id"]: state for state in self.workflow.store.states()}
        request_id = next(i for i in states if i != self.prepared["id"])
        self.assertEqual("published", states[request_id]["phase"])
        remote_tip = gitops.remote_tip(self.repository, "topic/qa")
        self.assertTrue(gitops.ancestor(self.repository, gitops.sha(self.repository, "HEAD"), remote_tip))

    def test_approval_without_cloud_instruction_stops_before_re_qa_request(self):
        self.approve(f"この計画で修正して。{COMMIT_PHRASE}")
        self.fix_product()
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("stopped", result["status"])
        self.assertIn(CLOUD, result["reason"])
        self.assertEqual(["commit", "submit"], result["completed"])
        self.assertEqual(1, len(self.workflow.store.states()))

    def test_approved_fix_over_line_limit_is_still_committed(self):
        self.approve(APPROVAL)
        (self.repository / "src/product.py").write_text("".join(f"line {i}\n" for i in range(60)))
        head_before = gitops.sha(self.repository, "HEAD")
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("completed", result["status"], result)
        self.assertEqual("commit", result["completed"][0])
        self.assertIn("src/product.py", run_git(self.repository, "log", "--name-only", "--format=", f"{head_before}..HEAD"))

    def test_change_outside_approved_paths_is_left_out_of_commit_and_recorded(self):
        self.approve(APPROVAL)
        self.fix_product()
        (self.repository / "src/other.py").write_text("unrelated\n")
        head_before = gitops.sha(self.repository, "HEAD")
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("completed", result["status"], result)
        recorded = self.workflow.store.select(self.prepared["id"])["loop"]["done"]["commit"]
        self.assertEqual(["src/other.py"], recorded["left_out"])
        committed = run_git(self.repository, "log", "--name-only", "--format=", f"{head_before}..HEAD")
        self.assertIn("src/product.py", committed)
        self.assertNotIn("src/other.py", committed)
        self.assertIn("src/other.py", run_git(self.repository, "status", "--porcelain"))

    def test_changed_contract_stops_before_commit(self):
        self.approve(APPROVAL)
        self.fix_product()
        plan_path = self.repository / self.workflow.store.select(self.prepared["id"])["plan"]["path"]
        plan_path.write_text(plan_path.read_text(encoding="utf-8") + "\n追記\n", encoding="utf-8")
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("stopped", result["status"])
        self.assertIn("完了条件・受入基準・確認方法の変更", result["reason"])
        self.assertEqual([], result["completed"])

    def test_loop_refuses_approval_that_is_not_in_the_user_prompt_log(self):
        self.workflow.approve(self.prepared["id"], APPROVAL, self.planned["plan_hash"], ["src/product.py"])
        self.fix_product()
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("stopped", result["status"])
        self.assertIn("利用者の発言として確認できません", result["reason"])
        self.assertEqual([], result["completed"])

    def test_waiting_approval_returns_the_plan_reference_and_body(self):
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("waiting_approval", result["status"])
        self.assertEqual(self.planned["plan_hash"], result["plan"]["hash"])
        self.assertIn("QA-F01", result["plan"]["body"])

    def test_status_reports_loop_progress_after_a_stop(self):
        self.approve(f"この計画で修正して。{COMMIT_PHRASE}")
        self.fix_product()
        self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        status = self.workflow.status(self.prepared["id"])
        self.assertEqual(["commit", "submit"], status["loop"]["completed"])
        self.assertEqual("push", status["loop"]["next"])

    def test_rejected_push_stops_before_any_re_qa_request(self):
        hook = self.remote / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        self.approve(APPROVAL)
        self.fix_product()
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("failed", result["status"])
        self.assertEqual(["commit", "submit"], result["completed"])
        self.assertEqual(1, len(self.workflow.store.states()))

    def test_publication_can_be_authorized_after_a_commit_only_stop(self):
        self.approve(f"この計画で修正して。{COMMIT_PHRASE}")
        self.fix_product()
        stopped = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("stopped", stopped["status"])
        record_user_prompt(self.repository, CLOUD)
        self.workflow.authorize_publish(self.prepared["id"], CLOUD)
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("completed", result["status"], result)
        self.assertEqual(["commit", "submit", "push", "ancestry", "requa-request", "finalize", "publish"], result["completed"])

    def test_authorization_is_refused_when_the_head_has_changed(self):
        self.approve(f"この計画で修正して。{COMMIT_PHRASE}")
        self.fix_product()
        self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        record_user_prompt(self.repository, CLOUD)
        self.workflow.authorize_publish(self.prepared["id"], CLOUD)
        (self.repository / "notes.txt").write_text("later change\n")
        run_git(self.repository, "add", "notes.txt")
        run_git(self.repository, "commit", "-m", "later change")
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("stopped", result["status"])
        self.assertEqual(1, len(self.workflow.store.states()))

    def test_publication_authorization_must_be_an_utterance_in_the_log(self):
        self.approve(f"この計画で修正して。{COMMIT_PHRASE}")
        with self.assertRaisesRegex(QAError, "発言として確認できません"):
            self.workflow.authorize_publish(self.prepared["id"], CLOUD)

    def test_retry_after_a_failed_progress_save_does_not_duplicate_the_re_qa_request(self):
        from unittest import mock
        from qa_workflow.store import QAError as StoreQAError
        original = Workflow._record_loop
        failed_once = {"done": False}

        def flaky(workflow, request, progress, failed):
            if "requa-request" in progress and not failed_once["done"]:
                failed_once["done"] = True
                raise StoreQAError("progress save failed")
            return original(workflow, request, progress, failed)

        self.approve(APPROVAL)
        self.fix_product()
        with mock.patch.object(Workflow, "_record_loop", flaky):
            first = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("failed", first["status"])
        second = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("completed", second["status"], second)
        children = [st for st in self.workflow.store.states() if st.get("previous") == self.prepared["id"]]
        self.assertEqual(1, len(children))
        approval_head = self.workflow.store.select(self.prepared["id"])["approval"]["head"]
        fix_commits = run_git(self.repository, "log", "--format=%s", f"{approval_head}..HEAD").splitlines()
        self.assertEqual(1, fix_commits.count(f"Yip: {self.prepared['id']} 修正"))

    def test_secret_in_outgoing_commit_stops_the_push_before_anything_is_published(self):
        self.approve(APPROVAL)
        (self.repository / "src/product.py").write_text("api_" + "token" + " = " + "'" + "real-value-1234" + "'\n")
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("failed", result["status"], result)
        self.assertIn("機密情報", result["reason"])
        self.assertEqual(["commit", "submit"], result["completed"])
        self.assertIsNone(gitops.remote_tip(self.repository, "topic/qa"))
        self.assertEqual(1, len(self.workflow.store.states()))

    def test_clean_outgoing_commit_is_still_pushed(self):
        self.approve(APPROVAL)
        self.fix_product()
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("completed", result["status"], result)
        self.assertIsNotNone(gitops.remote_tip(self.repository, "topic/qa"))

    def test_failed_progress_save_after_any_side_effect_does_not_duplicate_it(self):
        from unittest import mock
        for stage in ("commit", "push", "publish"):
            with self.subTest(stage=stage):
                self.tearDown()
                self.setUp()
                original = Workflow._record_loop
                failed_once = {"done": False}

                def flaky(workflow, request, progress, failed, stage=stage):
                    if stage in progress and not failed_once["done"]:
                        failed_once["done"] = True
                        raise QAError("progress save failed")
                    return original(workflow, request, progress, failed)

                self.approve(APPROVAL)
                self.fix_product()
                head_before = gitops.sha(self.repository, "HEAD")
                with mock.patch.object(Workflow, "_record_loop", flaky):
                    first = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
                self.assertEqual("failed", first["status"], first)
                second = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
                self.assertEqual("completed", second["status"], second)
                children = [st for st in self.workflow.store.states() if st.get("previous") == self.prepared["id"]]
                self.assertEqual(1, len(children))
                subjects = run_git(self.repository, "log", "--format=%s", f"{head_before}..HEAD").splitlines()
                self.assertEqual(1, subjects.count(f"Yip: {self.prepared['id']} 修正"))
                tip = gitops.remote_tip(self.repository, "topic/qa")
                self.assertTrue(gitops.ancestor(self.repository, gitops.sha(self.repository, "HEAD"), tip))

    def test_finding_repeated_from_the_previous_cycle_stops_the_loop(self):
        self.approve(APPROVAL)
        self.fix_product()
        self.workflow._carry_loop_history(self.prepared["id"], [["QA-F01"]])
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("stopped", result["status"], result)
        self.assertIn("同一指摘", result["reason"])
        self.assertEqual([], result["completed"])

    def test_authorized_continue_lets_a_repeated_finding_proceed(self):
        self.approve(APPROVAL)
        self.fix_product()
        self.workflow._carry_loop_history(self.prepared["id"], [["QA-F01"]])
        stopped = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("stopped", stopped["status"], stopped)
        record_user_prompt(self.repository, "反復を承知で続行する")
        self.workflow.authorize_continue(self.prepared["id"], "反復を承知で続行する")
        recorded = self.workflow.store.select(self.prepared["id"])["continue_authorization"]
        self.assertEqual(["QA-F01"], recorded["ids"])
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("completed", result["status"], result)

    def test_continue_authorization_must_be_an_utterance_in_the_log(self):
        self.approve(APPROVAL)
        self.workflow._carry_loop_history(self.prepared["id"], [["QA-F01"]])
        with self.assertRaisesRegex(QAError, "発言として確認できません"):
            self.workflow.authorize_continue(self.prepared["id"], "反復を承知で続行する")

    def test_continue_authorization_needs_a_continue_statement(self):
        self.approve(APPROVAL)
        self.workflow._carry_loop_history(self.prepared["id"], [["QA-F01"]])
        record_user_prompt(self.repository, "了解")
        with self.assertRaisesRegex(QAError, "続行"):
            self.workflow.authorize_continue(self.prepared["id"], "了解")

    def test_continue_authorization_is_refused_when_nothing_repeats(self):
        self.approve(APPROVAL)
        self.workflow._carry_loop_history(self.prepared["id"], [["QA-F99"]])
        record_user_prompt(self.repository, "反復を承知で続行する")
        with self.assertRaisesRegex(QAError, "反復している指摘がありません"):
            self.workflow.authorize_continue(self.prepared["id"], "反復を承知で続行する")

    def test_continue_authorization_is_refused_before_plan_approval(self):
        record_user_prompt(self.repository, "反復を承知で続行する")
        with self.assertRaisesRegex(QAError, "承認"):
            self.workflow.authorize_continue(self.prepared["id"], "反復を承知で続行する")

    def test_loop_proceeds_when_the_previous_cycle_had_other_findings(self):
        self.approve(APPROVAL)
        self.fix_product()
        self.workflow._carry_loop_history(self.prepared["id"], [["QA-F99"]])
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("completed", result["status"], result)

    def test_loop_history_is_stored_as_plain_lists_for_the_next_cycle(self):
        self.approve(APPROVAL)
        self.fix_product()
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("completed", result["status"], result)
        child = next(st for st in self.workflow.store.states() if st.get("previous") == self.prepared["id"])
        self.assertEqual([["QA-F01"]], child["loop_history"])

    def test_approval_can_be_updated_to_include_the_commit_scope_before_submission(self):
        self.approve("この計画で修正して。")
        self.approve(f"この計画で修正して。{COMMIT_PHRASE}")
        self.assertEqual(f"この計画で修正して。{COMMIT_PHRASE}", self.workflow.store.select(self.prepared["id"])["approval"]["message"])


if __name__ == "__main__":
    unittest.main()
