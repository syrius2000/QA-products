"""QA依頼、結果確認、修正承認、再QAのローカル操作。"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from . import gitops, review
from .github import GitHub
from .store import Store, QAError, atomic, digest, fingerprint, header, now, relative, safe_path

REVIEWER_MATERIAL_PATHS = [
    "quality-loop/skills/quality-qa/SKILL.md",
    "quality-loop/skills/quality-qa/references/reviewer_contract.md",
]


def submitted_product_paths(state: dict) -> list[str]:
    return sorted(set(state["products"]) | set(state.get("plan", {}).get("paths", [])))


def verify_submission_snapshot(root: Path, state: dict, reviewed: str | None = None) -> None:
    """Reject product changes made after submission before they become a re-QA target."""
    submission = state.get("submission")
    expected = submission.get("product_snapshot") if isinstance(submission, dict) else None
    paths = submitted_product_paths(state)
    if (
        not isinstance(expected, dict)
        or submission.get("product_paths") != paths
        or set(expected) != set(paths)
    ):
        raise QAError("修正提出時の全製品対象スナップショットがありません", "提出内容を確認してから再QA対象を確定してください")
    if gitops.snapshot(root, paths) != expected:
        raise QAError("修正提出後に製品対象が変更されています", "未承認変更を除くか、修正計画を更新して再承認してください")
    if reviewed and gitops.tree_snapshot(root, reviewed, paths) != expected:
        raise QAError("再QAの対象commitが修正提出済みスナップショットと一致しません", "提出済み内容だけをcommitしてから再QAしてください")


def reviewer_materials(root: Path, target: str) -> list[dict]:
    snapshot = gitops.tree_snapshot(root, target, REVIEWER_MATERIAL_PATHS)
    return [
        {"path": path, "sha256": snapshot[path]["hash"] if snapshot[path] else "不足"}
        for path in REVIEWER_MATERIAL_PATHS
    ]


class Workflow:
    def __init__(self, directory: Path):
        self.root = gitops.root_for(directory)
        self.store = Store(self.root, gitops.git_directory(self.root))

    def _load(self, request, revision=None):
        state = self.store.select(request)
        if revision is not None and state["revision"] != revision:
            raise QAError("状態が更新されています", "状況を読み直してから操作してください")
        return state

    def _save(self, s, event):
        self.store.save(s, s["revision"], event)
        return self.describe(s)

    @staticmethod
    def _formal(s):
        if s["reviewed"] is None:
            raise QAError("対象未確定の下書きでは進めません", "表示済み対象のローカルcommitまたは対象commit確認が必要です")

    @staticmethod
    def _active(s):
        if s["pending_correction"]:
            raise QAError("訂正待ちの間は旧レビューで進めません", "予約先へ訂正版を提出し、構造・内容を確認してください")
        for r in s["reviews"]:
            if r["hash"] == s["active_review"] and r.get("content_checked") and not r["issues"]:
                return r
        raise QAError("有効なレビューがありません", "レビューの構造と内容を確認してください")

    def _register(self, s, slug, label, extension="md"):
        p = self.store.allocate(slug, extension, s["operational"])
        if p in s["products"]:
            raise QAError("製品と運用成果物の保存先が重複しています")
        s["operational"][p] = label
        return p

    def status(self, request=None):
        return self.describe(self.store.select(request))

    def describe(self, s):
        phase = s["phase"]
        rejected_scan = s.get("publication_scan", {}).get("scan_result") == "REJECTED"
        hide_artifact_content = False
        if rejected_scan:
            actor = "ユーザー"
            action = s["publication_scan"].get("recovery_action", "原因を除いた新しいQA依頼を作成し、記録済み対象SHAを再利用してください")
            reason = "最終公開走査で拒否されました。既存の依頼と状態は保持されています"
            artifact = s["state_path"]
            hide_artifact_content = True
        elif s["pending_correction"] or phase == "invalid":
            actor, action, reason = "ユーザー→別のレビュー担当", "訂正依頼文を渡してください", "結果の不備または訂正待ちです"
            artifact = (s["pending_correction"] or {}).get("invite")
        elif phase == "draft":
            actor, action, reason = "ユーザー", "表示対象のローカルcommitまたはクラウド公開を指示してください", "対象版が未確定です"
            artifact = s["invite"]
        elif phase == "content_pending":
            actor, action, reason = "ローカル担当", "元要求と対象版の根拠に照らして内容を確認してください", "取得・構造確認は意味の妥当性を証明しません"
            artifact = s["reviews"][-1]["path"]
        elif phase == "planned":
            actor, action, reason = "ユーザー", "この計画で修正して、と指示してください", "製品修正は計画承認後です"
            artifact = s["plan"]["path"]
        elif phase == "approved":
            actor, action, reason = "ローカル実装担当", "承認対象を修正・確認し、提出記録を残してください", "修正提出は独立検証と別です"
            artifact = s["plan"]["path"]
        elif phase == "submitted":
            actor, action, reason = "ユーザー→別のレビュー担当", "再QAに出して、と宛先付きで指示してください", "前回指摘を独立して確認する必要があります"
            artifact = s["invite"]
        elif phase == "decision":
            actor, action, reason = "ユーザー", "必要なら既定ブランチへの統合を別途指示してください", "終了判断を記録済みです。統合と公開は別操作です"
            artifact = s.get("decision", {}).get("path")
        elif phase == "reviewed":
            r = self._active(s)
            if r["parsed"].get("required_checks") != "完了" or r["parsed"].get("gate") not in {"PASS", "HOLD", "FAIL"}:
                actor, action, reason = "ユーザー→確認担当", "不足する必須確認を依頼するか残余事項を判断してください", "必要な動作確認が未完了です"
            elif self.blocking(s):
                actor, action, reason = "ローカル担当", "指摘別の修正計画を準備してください", "重大問題または要求未達が残っています"
            elif r["parsed"].get("gate") != "PASS":
                actor, action, reason = "ユーザー→確認担当", "結論と残る確認を担当へ確認してください", "PASS以外の結果から終了候補には進めません"
            else:
                actor, action, reason = "ユーザー", "残余事項を確認して終了判断を指示してください", "技術的な終了候補です。自動受入は行いません"
            artifact = r["path"]
        elif s["audience"] == "cloud" and phase == "prepared":
            actor, action, reason = "ユーザー", "クラウドQAに出して、と公開を指示してください", "依頼は準備済みで、公開確認は未完了です"
            artifact = s["invite"]
        else:
            actor, action, reason = "ユーザー→別のレビュー担当", "依頼文を渡し、指定先へレビューを提出してもらってください", "レビューを待っています"
            artifact = s["invite"]
        invitation = safe_path(self.root, artifact).read_text() if not hide_artifact_content and artifact and safe_path(self.root, artifact).is_file() else None
        return {"id": s["id"], "cycle": s["cycle"], "revision": s["revision"], "phase": phase, "reviewed": s["reviewed"], "next": {"担当": actor, "操作": action, "理由": reason, "必要入力": artifact or s["id"], "依頼文": invitation}, "issues": s["reviews"][-1]["issues"] if s["reviews"] else [], "plan_hash": s.get("plan", {}).get("hash"), "plan_paths": s.get("plan", {}).get("paths", []), "review_path": self._expected(s)["review_path"], "products": sorted(s["products"]), "state_path": s["state_path"], "checks": {"構造検査": "確認済み" if s["active_review"] else "未完了", "独立性": "担当・経路の記録。完全な証明ではない", "実クラウドQA": "結果の実行Evidenceを別途確認", "外部配置": "この操作では実施しない"}}

    def prepare(self, purpose: str, criteria: list[str], products: list[str], implementer: str, author: str, audience="cloud", assumptions="未指定", baseline=None, reviewed=None, repository=None, excluded=None, previous=None, required_tests=None, checks=None, check_contract_approval=None):
        if not purpose.strip() or not criteria or not all(isinstance(x, str) and x.strip() for x in criteria) or not products or not implementer.strip() or audience not in {"local", "cloud"}:
            raise QAError("目的・受入基準・対象ファイル・実装担当・宛先が必要です")
        for p in products: relative(p)
        excluded = excluded or {}
        if any(not isinstance(reason, str) or not reason.strip() for reason in excluded.values()):
            raise QAError("対象外の理由が必要です")
        for p in excluded: relative(p)
        with self.store.transaction():
            old = self._load(previous) if previous else None
            if old:
                self._formal(old); self._active(old)
                if old["phase"] != "submitted":
                    raise QAError("修正提出後に再QAを依頼してください")
                purpose, criteria, assumptions = old["purpose"], old["criteria"], old["assumptions"]
                verify_submission_snapshot(self.root, old, gitops.sha(self.root, reviewed) if reviewed else None)
            state_path = self.store.allocate("qa_state", "json")
            number = re.search(r"_(\d{3})_", state_path).group(1)
            branch = gitops.git(self.root, "branch", "--show-current")
            if not branch:
                raise QAError("開発ブランチを選んでください")
            repo = gitops.repository(self.root, repository)
            base = old["reviewed"] if old else gitops.baseline(self.root, baseline)
            initial = old["initial_baseline"] if old else base
            target = gitops.sha(self.root, reviewed or "HEAD")
            if not gitops.ancestor(self.root, initial, target) or not gitops.ancestor(self.root, base, target):
                raise QAError("基準が対象commitの祖先ではありません")
            pending = not reviewed and bool(set(products) & gitops.dirty(self.root))
            if checks is not None:
                check_contract = checks
                if old:
                    previous_checks = old.get("checks", [])
                    previous_required = {c["id"]: c for c in previous_checks if c.get("required")}
                    next_by_id = {c.get("id"): c for c in checks if isinstance(c, dict)}
                    weakened = [check_id for check_id, check in previous_required.items() if next_by_id.get(check_id) != check]
                    if weakened:
                        raise QAError("再QAで既存の必須checkが削除または変更されています", "必須checkを完全に維持してください: " + ", ".join(sorted(weakened)))
                    if checks != previous_checks:
                        old_hash = fingerprint(previous_checks)
                        new_hash = fingerprint(checks)
                        approved = (
                            isinstance(check_contract_approval, str)
                            and bool(re.search(r"(?:契約.{0,12}(?:変更|追加|更新|見直し)|(?:check|確認|検証).{0,24}契約.{0,12}(?:変更|追加|更新|見直し))", check_contract_approval, re.I))
                            and old_hash in check_contract_approval
                            and new_hash in check_contract_approval
                        )
                        if not approved:
                            raise QAError("再QAで実行check契約が変わっています", f"旧契約hash {old_hash} と新契約hash {new_hash} を含む明示承認が必要です")
            else:
                check_contract = old.get("checks", []) if old else []
                if old and old.get("required_tests") and not check_contract:
                    raise QAError("旧形式の自由文必須確認を安全に再QAへ移せません", "各確認をID・argv・必須性・cwd・env・timeout・期待結果の構造化checkへ直し、再QA依頼を作成してください")
            s = {"schema": "unified-qa-workflow-v1", "id": f"QA-{number}", "cycle": old["cycle"]+1 if old else 1, "revision": 1, "state_path": state_path, "repository": repo, "branch": branch, "initial_baseline": initial, "baseline": base, "reviewed": None if pending else target, "purpose": purpose, "criteria": criteria, "assumptions": assumptions, "requirements_hash": fingerprint([purpose, assumptions, criteria]), "reviewer_materials": reviewer_materials(self.root, target), "products": {p: "明示された製品対象" for p in products}, "operational": dict(old["operational"]) if old else {}, "excluded": excluded, "snapshot": gitops.snapshot(self.root, products) if pending else gitops.tree_snapshot(self.root, target, products), "phase": "draft" if pending else "prepared", "audience": audience, "implementer": implementer, "author": author, "invite": "", "review_path": "", "reviews": [], "active_review": None, "pending_correction": None, "unresolved": copy.deepcopy(old["unresolved"]) if old else {}, "events": [], "checks": check_contract, "required_tests": [], "previous": old["id"] if old else None, "published": None, "history_reviews": copy.deepcopy(old.get("history_reviews", []) + old["reviews"]) if old else [], "published_paths": list(old.get("published_paths", [])) if old else []}
            if old and checks is not None and checks != old.get("checks", []):
                previous_checks = copy.deepcopy(old.get("checks", []))
                previous_by_id = {c["id"]: c for c in previous_checks}
                approved_by_id = {c["id"]: c for c in check_contract}
                s["check_contract_approval"] = {
                    "message": check_contract_approval,
                    "previous": previous_checks,
                    "approved": copy.deepcopy(check_contract),
                    "previous_hash": fingerprint(previous_checks),
                    "approved_hash": fingerprint(check_contract),
                    "diff": {
                        "added": sorted(set(approved_by_id) - set(previous_by_id)),
                        "removed": sorted(set(previous_by_id) - set(approved_by_id)),
                        "changed": sorted(k for k in set(previous_by_id) & set(approved_by_id) if previous_by_id[k] != approved_by_id[k]),
                    },
                    "at": now(),
                }
            if old:
                s["products"] = {**old["products"], **s["products"]}
                s["excluded"] = {**old["excluded"], **excluded}
                if pending:
                    s["snapshot"] = gitops.snapshot(self.root, s["products"])
            s["operational"][state_path] = "ローカル状態"
            s["invite"] = self._register(s, "qa_invite", "QA依頼")
            s["review_path"] = self._register(s, "qa_review", "レビュー予約先")
            s["classification"] = gitops.classify(self.root, initial, base, target, s["products"], s["operational"], s["excluded"])
            if set(s["products"]) & set(s["operational"]):
                raise QAError("製品と運用成果物の分類が重複しています")
            self.store.validate(s)
            self.store.preserve(s["invite"], review.invite(s).encode())
            s["invite_hash"] = digest(safe_path(self.root, s["invite"]).read_bytes())
            self.store.save(s)
            if old:
                old["superseded"] = s["id"]
                self.store.save(old, old["revision"], "再QA依頼作成")
            return self.describe(s)

    def _finalize(self, s, target):
        if gitops.tree_snapshot(self.root, target, s["products"]) != s["snapshot"]:
            raise QAError("commit内容が下書きと一致しません")
        if not gitops.ancestor(self.root, s["baseline"], target):
            raise QAError("確定対象は差分基準の後続である必要があります")
        s["classification"] = gitops.classify(self.root, s["initial_baseline"], s["baseline"], target, s["products"], s["operational"], s["excluded"])
        s["reviewer_materials"] = reviewer_materials(self.root, target)
        p = safe_path(self.root, s["invite"])
        if digest(p.read_bytes()) != s["invite_hash"]:
            raise QAError("下書き依頼が外部で変更されています")
        s["reviewed"] = target; s["phase"] = "prepared"
        atomic(p, review.invite(s).encode())
        s["invite_hash"] = digest(p.read_bytes())

    def finalize(self, request, target=None, approval=None, approved_paths=None, revision=None):
        with self.store.transaction():
            s = self._load(request, revision)
            if s["reviewed"]:
                if target and gitops.sha(self.root, target) != s["reviewed"]:
                    raise QAError("正式依頼の対象SHAは書き換えられません")
                return self.describe(s)
            if target:
                target = gitops.sha(self.root, target)
            else:
                if not approval or not re.search(r"commit|コミット", approval, re.I) or set(approved_paths or []) != set(s["products"]):
                    raise QAError("表示対象への明示的なローカルcommit指示が必要です")
                target = gitops.commit_paths(self.root, s["products"], s["snapshot"], f"QA target {s['id']}")
                s["local_commit_approval"] = {"message": approval, "paths": sorted(approved_paths), "at": now()}
            self._finalize(s, target)
            return self._save(s, "対象確定（pushなし）")

    def publish(self, request, message: str, approved_paths: list[str], revision=None):
        with self.store.transaction():
            s = self._load(request, revision)
            prior_scan = s.get("publication_scan", {})
            if prior_scan.get("scan_result") == "REJECTED":
                raise QAError(
                    "最終公開走査で拒否済みの依頼は再利用できません",
                    prior_scan.get("recovery_action", "拒否理由を解消した新しいQA依頼を作成し、記録済み対象SHAを指定してください"),
                )
            if s["audience"] != "cloud" or not re.search(r"クラウド.*(?:出して|公開)|cloud.*(?:publish|QA)", message, re.I):
                raise QAError("クラウド公開の実際のユーザー指示が必要です")
            required = set(s["products"]) | {s["invite"]}
            allowed = set(approved_paths)
            for p in allowed: relative(p)
            if not required <= allowed or set(s["operational"]) & allowed - {s["invite"]}:
                raise QAError("公開対象集合が表示した製品と依頼の集合に一致しません")
            if allowed != required:
                raise QAError("公開対象へ未定義の範囲を追加できません")
            current_products = gitops.snapshot(self.root, s["products"])
            if current_products != s["snapshot"]:
                raise QAError("QA対象snapshotが依頼固定時点から変化しています", "対象とEvidenceを再確認して依頼を作り直してください")
            content_findings = gitops.publication_findings(self.root, set(s["products"]) | {s["invite"]})
            if content_findings:
                raise QAError("公開対象に機密情報または個人ローカルパスの疑いがあります", "検出: " + ", ".join(content_findings) + "。公開前に対象を修正してください")
            contracts = s.get("checks", [])
            if any(check.get("required") for check in contracts):
                evidence = s.get("check_evidence")
                if (
                    not isinstance(evidence, dict)
                    or evidence.get("snapshot_hash") != fingerprint(current_products)
                    or evidence.get("contract_hash") != fingerprint(contracts)
                    or any(item.get("status") != "PASS" for item in evidence.get("results", []) if next((c.get("required") for c in contracts if c["id"] == item.get("id")), False))
                    or {item.get("id") for item in evidence.get("results", [])} != {item["id"] for item in contracts}
                ):
                    raise QAError("必須checkの成功Evidenceが対象snapshotと一致しません", "verifyでcheckを実行し、全必須checkのPASS Evidenceを記録してください")
            # 過去の公開済み運用成果物も履歴には現れる。新規送出は承認集合だけ。
            history_allowed = allowed | set(s.get("published_paths", []))
            flight = gitops.preflight(self.root, s, history_allowed)
            s["publish_approval"] = {"message": message, "paths": sorted(allowed), "preflight": flight, "at": now()}
            if s["reviewed"] is None:
                target = gitops.commit_paths(self.root, s["products"], s["snapshot"], f"QA target {s['id']}")
                self._finalize(s, target)
            if digest(safe_path(self.root, s["invite"]).read_bytes()) != s["invite_hash"]:
                raise QAError("正式依頼本文が変更されています")
            # finalize may rewrite the invitation with the fixed target SHA and material hashes.
            # Scan and pin the final bytes that are about to be committed.
            invite_bytes = safe_path(self.root, s["invite"]).read_bytes()
            final_paths = set(s["products"]) | {s["invite"]}
            final_snapshot = gitops.snapshot(self.root, final_paths)
            expected_final_snapshot = dict(current_products)
            expected_final_snapshot[s["invite"]] = {"mode": "100644", "hash": digest(invite_bytes)}
            recovery_action = (
                f"{s['id']}のstateと依頼本文を編集せず保持してください。原因を除いた新しいQA依頼/stateを作り、"
                f"--reviewed {s['reviewed']} を指定してこの製品対象commitを再利用してください。"
                "新しい依頼の本文を確認するまで公開しないでください。"
            )
            s["publication_scan"] = {
                "product_snapshot_hash": fingerprint(current_products),
                "invite_hash": digest(invite_bytes),
                "reviewer_materials_hash": fingerprint(s.get("reviewer_materials", [])),
                "check_contract_hash": fingerprint(contracts),
                "reviewed": s["reviewed"],
                "scan_result": "PENDING",
                "stage": "final-publication-scan",
                "started_at": now(),
                "recovery_action": recovery_action,
            }
            # Target SHAと最終依頼のhashを、拒否し得る最終走査より先に永続化する。
            self.store.save(s, s["revision"], "対象SHA・最終依頼hashを走査前保存")
            s = self.store.read(s["state_path"])
            if final_snapshot != expected_final_snapshot:
                self._record_final_scan_rejection(s, "snapshot-validation", ["snapshot-mismatch"])
                raise QAError(
                    "最終QA依頼または製品対象が公開検査中に変更されました",
                    recovery_action,
                )
            content_findings = gitops.publication_findings(self.root, final_paths)
            if content_findings:
                self._record_final_scan_rejection(s, "final-publication-scan", content_findings)
                raise QAError(
                    "最終公開対象に機密情報または個人ローカルパスの疑いがあります",
                    "検出分類: " + ", ".join(content_findings) + "。" + recovery_action,
                )
            s["publication_scan"].update({"scan_result": "PASS", "completed_at": now(), "findings": []})
            self.store.save(s, s["revision"], "最終公開走査成功を保存")
            s = self.store.read(s["state_path"])
            scanned_invite_snapshot = {s["invite"]: final_snapshot[s["invite"]]}
            try:
                invite_commit = gitops.commit_paths(self.root, [s["invite"]], scanned_invite_snapshot, f"QA invite {s['id']}")
                committed_invite = gitops.tree_snapshot(self.root, invite_commit, [s["invite"]])[s["invite"]]
                if not committed_invite or committed_invite["hash"] != s["publication_scan"]["invite_hash"]:
                    raise QAError("公開走査済みQA依頼と依頼commit内の内容が一致しません")
                s["invite_commit"] = invite_commit
                self.store.save(s, s["revision"], "依頼commit確認")
                s = self.store.read(s["state_path"])
                tip = gitops.push(self.root, s, invite_commit)
            except QAError as e:
                s["publish_error"] = str(e)
                self.store.save(s, s["revision"], "公開未完了・再試行待ち")
                raise QAError(str(e), f"{s['id']}の公開を再試行してください。QA実行は未完了です") from e
            s["published"] = {"tip": tip, "invite_commit": invite_commit, "reviewed": s["reviewed"], "at": now()}
            s["publication_scan"]["invite_commit"] = invite_commit
            s["published_paths"] = sorted(history_allowed)
            if s["phase"] in {"prepared", "published"}:
                s["phase"] = "published"
            s.pop("publish_error", None)
            return self._save(s, "topic公開・到達可能性確認")

    def _record_final_scan_rejection(self, s, stage, findings):
        scan = s["publication_scan"]
        scan.update({
            "scan_result": "REJECTED",
            "stage": stage,
            "findings": sorted(set(findings)),
            "completed_at": now(),
        })
        s["publish_error"] = "最終公開走査拒否: " + ", ".join(scan["findings"])
        self.store.save(s, s["revision"], "最終公開走査拒否と再開案内を保存")

    def verify(self, request, revision=None):
        """Execute only the explicitly declared argv checks and bind evidence to this product snapshot."""
        with self.store.transaction():
            s = self._load(request, revision)
            if not s.get("checks"):
                raise QAError("実行するcheck契約がありません")
            before = gitops.snapshot(self.root, s["products"])
            if before != s["snapshot"]:
                raise QAError("check実行前に製品snapshotが変化しています", "対象とQA依頼を再固定してください")
            results = gitops.execute_checks(self.root, s["checks"])
            after = gitops.snapshot(self.root, s["products"])
            if after != before:
                raise QAError("check実行中に製品対象が変更されました", "変更を確認し、新しい対象snapshotで依頼してください")
            s["check_evidence"] = {
                "snapshot_hash": fingerprint(before), "contract_hash": fingerprint(s["checks"]),
                "results": results, "recorded_at": now(),
            }
            return self._save(s, "QA対象に結び付けたcheck実行Evidence")

    def handoff(self, request, revision=None):
        with self.store.transaction():
            s = self._load(request, revision); self._formal(s)
            if s["phase"] not in {"prepared", "published", "waiting"}:
                raise QAError("レビュー取得後は過去の手渡し状態へ戻せません")
            if s["audience"] == "cloud" and not s["published"]:
                raise QAError("クラウド公開の確認がまだありません")
            s["phase"] = "waiting"
            return self._save(s, "ユーザーが依頼を手渡し")

    @staticmethod
    def _expected(s):
        return s["pending_correction"] or {"version": 1, "correction_id": "なし", "replaces": "なし", "review_path": s["review_path"]}

    def acquire(self, request, body: Path | None = None, branch=None, pr=None, adapter=None, revision=None):
        # 外部の読取り中もrevisionの対応を保つ。取得失敗時は状態を更新しない。
        s = self._load(request, revision); self._formal(s)
        path = self._expected(s)["review_path"]
        if body is not None:
            if body.is_symlink() or not body.is_file(): raise QAError("レビュー本文は通常ファイルを指定してください")
            raw = body.read_bytes()
            source = {"kind": "body", "commit": None, "path": path, "acquired": now(), "limit": "取得元commit未確認"}
        else:
            raw, source = (adapter or GitHub()).acquire(s["repository"], path, branch or s["branch"], pr)
        return self.ingest(request, raw, source, s["revision"])

    def ingest(self, request, raw: bytes, source: dict, revision=None):
        with self.store.transaction():
            s = self._load(request, revision); self._formal(s)
            raw_hash = digest(raw)
            existing = next((r for r in s["reviews"] if r["hash"] == raw_hash), None)
            if existing:
                source_added = source not in existing["sources"]
                if source_added:
                    existing["sources"].append(source)
                if existing is s["reviews"][-1] and existing.get("issues") and not existing.get("content_checked") and not s.get("pending_correction"):
                    expected = self._expected(s)
                    try:
                        parsed, issues = review.check(raw.decode("utf-8"), s, expected)
                    except UnicodeDecodeError:
                        parsed, issues = {}, ["レビューはUTF-8のMarkdownが必要です"]
                    existing.setdefault("validation_history", []).append({"at": now(), "issues": copy.deepcopy(existing["issues"])})
                    existing["parsed"], existing["issues"] = parsed, issues
                    s["phase"] = "invalid" if issues else "content_pending"
                    return self._save(s, "同一原文を現行validatorで再検査")
                if source_added:
                    return self._save(s, "同一原文の出典追加")
                return self.describe(s)
            expected = self._expected(s)
            if source.get("path") != expected["review_path"]:
                raise QAError("予約された返却パスではありません", f"{expected['review_path']}へ提出してください")
            if source.get("kind") != "body" and not re.fullmatch(r"[0-9a-f]{40}", str(source.get("commit"))):
                raise QAError("取得元commitの完全なSHAがありません")
            # 原文は解析に失敗しても保持。別内容で同名の場合はpreserveで拒否。
            self.store.preserve(expected["review_path"], raw)
            try:
                parsed, issues = review.check(raw.decode("utf-8"), s, expected)
            except UnicodeDecodeError:
                parsed, issues = {}, ["レビューはUTF-8のMarkdownが必要です"]
            entry = {"path": expected["review_path"], "hash": raw_hash, "sources": [source], "version": expected["version"], "correction_id": expected["correction_id"], "replaces": expected["replaces"], "parsed": parsed, "issues": issues, "content_checked": False}
            s["reviews"].append(entry)
            s["phase"] = "invalid" if issues else "content_pending"
            return self._save(s, "原文取得・構造検査")

    def confirm_content(self, request, evidence: str, checker: str, revision=None):
        with self.store.transaction():
            s = self._load(request, revision); self._formal(s)
            if not evidence.strip() or not checker.strip() or not s["reviews"]:
                raise QAError("内容確認の担当と元要求・対象版の根拠が必要です")
            r = s["reviews"][-1]
            expected = self._expected(s)
            if r["issues"] or r["version"] != expected["version"] or r["path"] != expected["review_path"]:
                raise QAError("不備または古いレビューを有効化できません", "訂正依頼を作成してください")
            if digest(safe_path(self.root, r["path"]).read_bytes()) != r["hash"]:
                raise QAError("取得原文が外部で変更されています")
            r["content_checked"] = True; r["content_evidence"] = evidence; r["checker"] = checker
            s["active_review"] = r["hash"]; s["pending_correction"] = None
            for fid, result in r["parsed"]["previous"].items():
                if result["result"] == "解消": s["unresolved"].pop(fid, None)
            for f in r["parsed"]["findings"]:
                if f.get("状態") == "OPEN": s["unresolved"][f["id"]] = f
                elif f["id"] in s["unresolved"]:
                    # 訂正版で状態CLOSEDとするだけでは以前の指摘を消さない。
                    pass
            s["phase"] = "reviewed"
            return self._save(s, "構造・内容確認後の有効版選択")

    def correction(self, request, reason: str, revision=None):
        with self.store.transaction():
            s = self._load(request, revision); self._formal(s)
            if not s["reviews"] or not reason.strip(): raise QAError("訂正対象の原文と具体的な不備／反証が必要です")
            latest = s["reviews"][-1]
            if s["pending_correction"] and s["pending_correction"]["replaces"] == latest["hash"]:
                return self.describe(s)
            p = self._register(s, "qa_correction", "訂正依頼")
            review_path = self._register(s, "qa_review", "訂正版レビュー予約先")
            correction = {"correction_id": f"{s['id']}-C{latest['version']:03d}", "version": latest["version"] + 1, "replaces": latest["hash"], "review_path": review_path, "invite": p, "reason": reason}
            s["pending_correction"] = correction; s["phase"] = "invalid"
            text = header("QA結果の訂正依頼", s["author"]) + f"元依頼: {s['invite']}\n\n依頼ID・対象版・基準・サイクル・要件は変更しません。原文は上書きせず `{review_path}` に完全な訂正版1ファイルを提出してください。\n\n訂正理由: {reason}\n\n検出された不備:\n" + "\n".join(f"- {x}" for x in latest["issues"])
            text += "\n\nGitHub公開は別の明示指示が必要です。本文手渡しも可能です。\n\n## 継承する依頼\n\n" + review.invite(s) + "\n\n## 訂正版の記載例\n\n````markdown\n" + review.template(s, expected=correction) + "\n````\n"
            self.store.preserve(p, text.encode())
            return self._save(s, "訂正ID・提出版・別保存先を予約")

    def publish_correction(self, request, message, approved_paths, revision=None):
        with self.store.transaction():
            s = self._load(request, revision)
            c = s["pending_correction"]
            if not c or s["audience"] != "cloud" or not re.search(r"(?:クラウド|訂正).*(?:公開|出して)", message):
                raise QAError("訂正依頼の明示的な公開指示が必要です")
            if set(approved_paths) != {c["invite"]}:
                raise QAError("訂正依頼だけを公開対象にしてください")
            findings = gitops.publication_findings(self.root, {c["invite"]})
            if findings:
                raise QAError("訂正依頼に機密情報または個人ローカルパスの疑いがあります", "検出: " + ", ".join(findings) + "。公開前に対象を修正してください")
            allowed = set(s.get("published_paths", [])) | {c["invite"]}
            gitops.preflight(self.root, s, allowed)
            commit = gitops.commit_paths(self.root, [c["invite"]], gitops.snapshot(self.root, [c["invite"]]), f"QA correction {c['correction_id']}")
            tip = gitops.push(self.root, s, commit)
            c["published"] = {"tip": tip, "commit": commit, "message": message}
            s["published_paths"] = sorted(allowed)
            return self._save(s, "訂正依頼を明示指示で公開")

    @staticmethod
    def blocking(s):
        return [fid for fid, f in s["unresolved"].items() if f.get("種別") == "要求未達" or (f.get("種別") == "不具合" and f.get("重大度") == "重大")]

    def plan(self, request, items: list[dict], revision=None):
        with self.store.transaction():
            s = self._load(request, revision); r = self._active(s)
            if s["phase"] not in {"reviewed", "planned"}:
                raise QAError("確認済みレビューから修正計画を作成してください")
            fields = ["id", "理解", "方針", "対象", "影響", "完了条件", "確認方法"]
            ids = set()
            for item in items:
                if not isinstance(item, dict) or any(not item.get(k) for k in fields) or item["id"] not in s["unresolved"] or item["id"] in ids:
                    raise QAError("指摘別の理解・方針・対象・影響・完了条件・確認方法が必要です")
                ids.add(item["id"])
                if not isinstance(item["対象"], list): raise QAError("計画の対象はパスの配列が必要です")
                for p in item["対象"]: relative(p)
            if set(self.blocking(s)) - ids:
                raise QAError("重大問題・要求未達の計画が不足しています")
            if not items: raise QAError("修正する指摘を指定してください")
            signature = fingerprint([r["hash"], items])
            if s.get("plan", {}).get("signature") == signature:
                return self.describe(s)
            p = self._register(s, "implementation_plan", "修正計画")
            text = header("QA指摘へのローカル修正計画", s["author"]) + f"依頼: {s['id']}\n元レビュー: {r['path']}\n\n計画確認だけでは製品修正を開始しません。「この計画で修正して」の明示指示を受けてから修正します。反証はレビュー原文の書換えではなく再確認依頼へ進めます。\n\n"
            for item in items:
                text += f"## {item['id']}\n\n" + "\n".join(f"- {k}: {item[k]}" for k in fields[1:]) + "\n\n"
            self.store.preserve(p, text.encode())
            paths = sorted({p for item in items for p in item["対象"]})
            planned_method = "\n".join(f"{item['id']}: {item['方針']}" for item in items)
            s["plan"] = {"path": p, "hash": digest(text.encode()), "signature": signature, "items": items, "paths": paths, "review_hash": r["hash"], "before": gitops.snapshot(self.root, paths), "dirty_before": gitops.snapshot(self.root, gitops.dirty(self.root)), "method": planned_method}
            s["approval"] = None; s["phase"] = "planned"
            return self._save(s, "指摘別修正計画（製品変更なし）")

    def approve(self, request, message: str, plan_hash: str, paths: list[str], revision=None):
        with self.store.transaction():
            s = self._load(request, revision); r = self._active(s)
            plan = s.get("plan")
            if not plan or s["phase"] != "planned" or not re.search(r"修正して|実装して|承認", message):
                raise QAError("対象計画に対する実際のユーザー承認が必要です")
            if plan_hash != plan["hash"] or digest(safe_path(self.root, plan["path"]).read_bytes()) != plan["hash"] or set(paths) != set(plan["paths"]) or r["hash"] != plan["review_hash"] or gitops.snapshot(self.root, plan["paths"]) != plan["before"]:
                raise QAError("計画・対象・レビューが承認時点と一致しません", "計画を更新して再承認を受けてください")
            s["approval"] = {"message": message, "plan_hash": plan_hash, "paths": sorted(paths), "at": now(), "head": gitops.sha(self.root, "HEAD")}
            s["phase"] = "approved"
            return self._save(s, "人の計画承認を記録")

    def submit(self, request, paths: list[str], evidence: str, unverified: list[str], method: str | None = None, revision=None):
        with self.store.transaction():
            s = self._load(request, revision); self._active(s)
            p = s.get("plan"); a = s.get("approval")
            if not a or s["phase"] not in {"approved", "submitted"}:
                raise QAError("修正承認がありません")
            if not evidence.strip() or not paths or not set(paths) <= set(a["paths"]):
                raise QAError("修正提出の対象と確認Evidenceが必要です")
            if digest(safe_path(self.root, p["path"]).read_bytes()) != a["plan_hash"] or not method or method.strip() != p["method"]:
                raise QAError("計画または実装方式が変わっています", "計画更新と再承認が必要です")
            head = gitops.sha(self.root, "HEAD")
            committed = gitops.changed(self.root, a["head"], head)
            current_dirty = gitops.dirty(self.root)
            outside = (committed | current_dirty | set(p["dirty_before"])) - set(a["paths"]) - set(s["operational"])
            for name in outside:
                if gitops.snapshot(self.root, [name])[name] != p["dirty_before"].get(name, gitops.tree_snapshot(self.root, a["head"], [name])[name]):
                    raise QAError(f"承認外の変更が検出されました: {name}", "変更範囲を確認し、計画更新と再承認へ戻ってください")
            changed_allowed = {name for name in a["paths"] if gitops.snapshot(self.root, [name])[name] != p["before"][name]}
            if changed_allowed - set(paths):
                raise QAError("実際の変更対象が修正提出に不足しています")
            product_paths = submitted_product_paths(s)
            product_snapshot = gitops.snapshot(self.root, product_paths)
            s["submission"] = {"paths": sorted(paths), "snapshot": gitops.snapshot(self.root, paths), "product_paths": product_paths, "product_snapshot": product_snapshot, "content_hash": fingerprint(product_snapshot), "head": head, "evidence": evidence, "unverified": unverified, "at": now(), "independently_verified": False}
            s["phase"] = "submitted"
            return self._save(s, "承認範囲の修正提出（独立検証前）")

    def requa(self, request, audience=None, revision=None, check_contract_approval=None, **kwargs):
        s = self._load(request, revision)
        if audience is None:
            raise QAError("再QAの宛先が未指定です", "ローカルかクラウドを指定してください")
        return self.prepare(s["purpose"], s["criteria"], sorted(set(s["products"]) | set(s.get("plan", {}).get("paths", []))), s["implementer"], s["author"], audience, previous=s["id"], repository=s["repository"], check_contract_approval=check_contract_approval, **kwargs)

    def assess_residual(self, request, message: str, reason: str, revision=None):
        with self.store.transaction():
            s = self._load(request, revision); r = self._active(s)
            if not reason.strip() or not re.search(r"残余|未検証|リスク", message) or not re.search(r"判断|受容|受け入|保留|承認", message):
                raise QAError("未検証・残余事項への実際のユーザー判断と理由が必要です")
            if s.get("residual_assessment", {}).get("message") == message and s["residual_assessment"].get("reason") == reason:
                return self.describe(s)
            path = self._register(s, "qa_residual", "未検証・残余事項のユーザー判断")
            text = header("未検証・残余事項の判断記録", s["author"]) + f"依頼: {s['id']}\nレビュー: {r['path']}\n\nユーザー発言: {message}\n\n判断の理由: {reason}\n\n必須確認の状態: {r['parsed']['required_checks']}\n結論: {r['parsed']['gate']}\n\nこの記録は追加検証や独立QAの実行証明ではありません。未検証と未解決指摘は保持し、終了候補へ自動的に進めません。\n"
            self.store.preserve(path, text.encode())
            s["residual_assessment"] = {"path": path, "message": message, "reason": reason, "review_hash": r["hash"], "at": now(), "unverified_preserved": True}
            return self._save(s, "ユーザーの残余判断を記録（検証状態は保持）")

    def decide(self, request, message: str, residual: str, revision=None):
        with self.store.transaction():
            s = self._load(request, revision); r = self._active(s)
            if self.blocking(s) or r["parsed"]["gate"] != "PASS" or r["parsed"]["required_checks"] != "完了":
                raise QAError("必要な検証または重要指摘が残っています", "追加確認または根拠付き残余事項判断を記録してください。検証済みにはしません")
            if not re.search(r"終了|受入|完了", message) or not residual.strip():
                raise QAError("終了判断のユーザー発言と残余事項の確認が必要です")
            p = self._register(s, "qa_decision", "ユーザー終了判断")
            text = header("QA終了判断の記録", s["author"]) + f"依頼: {s['id']}\n\nユーザー発言: {message}\n\n残余事項: {residual}\n\n次操作: 必要なら既定ブランチ `{gitops.default_branch(self.root)}` への統合を別途指示してください。この記録だけでmerge・push・外部配置・旧版削除は行いません。\n"
            self.store.preserve(p, text.encode())
            s["decision"] = {"message": message, "residual": residual, "path": p}; s["phase"] = "decision"
            return self._save(s, "ユーザーの終了判断（Git操作なし）")
