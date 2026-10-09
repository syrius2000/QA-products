from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from qa_workflow import gitops, review
from qa_workflow.repair_commit import COMMIT_PHRASE
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
        self.assertEqual(["commit", "submit", "requa-request", "finalize", "publish"], result["completed"])
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

    def test_change_over_line_limit_stops_before_commit(self):
        self.approve(APPROVAL)
        (self.repository / "src/product.py").write_text("".join(f"line {i}\n" for i in range(60)))
        head_before = gitops.sha(self.repository, "HEAD")
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("stopped", result["status"])
        self.assertIn("変更行数が上限を超える", result["reason"])
        self.assertEqual([], result["completed"])
        self.assertEqual(head_before, gitops.sha(self.repository, "HEAD"))

    def test_change_outside_approved_paths_stops_before_commit(self):
        self.approve(APPROVAL)
        self.fix_product()
        (self.repository / "src/other.py").write_text("unrelated\n")
        result = self.workflow.loop(self.prepared["id"], "空入力fixture成功")
        self.assertEqual("stopped", result["status"])
        self.assertIn("承認済み対象パス外の変更", result["reason"])
        self.assertEqual([], result["completed"])


if __name__ == "__main__":
    unittest.main()
