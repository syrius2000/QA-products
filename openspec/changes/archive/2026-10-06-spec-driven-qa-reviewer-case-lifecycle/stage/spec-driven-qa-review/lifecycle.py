"""Reviewer QA ケース ライフサイクル コア実装。"""

import datetime
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any, Optional

from shared_core.digest import handoff_content_digest as compute_handoff_content_digest, handoff_digests
from shared_core.state import can_transition, TRANSITIONS
from .allowlist import check_write_permission

VALID_PROFILES = {"lite", "standard", "strict", "proportional-home"}
VALID_PURPOSE_CLASSIFICATIONS = {"spec-required", "purpose-critical", "operational-hygiene", "out-of-scope"}
VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}
VALID_TERMINAL_STATUSES = {
    "accepted",
    "accepted-with-residual-risk",
    "conditionally-accepted",
    "rejected",
    "blocked-insufficient-evidence",
    "adjudication-required",
}

PROFILE_CYCLE_LIMITS = {
    "lite": 1,
    "standard": 2,
    "strict": 3,
    "proportional-home": 2,
}


def get_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()


def parse_findings_list(text: str) -> list[dict[str, Any]]:
    """findings.yaml から各 Finding ブロックを正確に抽出・辞書化する軽量パーサー。"""
    findings = []
    blocks = re.split(r"(?m)^  - id:\s*", text)
    for block in blocks[1:]:
        lines = block.strip().splitlines()
        first_line = lines[0].strip()
        fid = first_line.split()[0] if first_line else ""
        item = {"id": fid}
        for line in lines[1:]:
            m = re.match(r"^    ([a-z_]+):\s*(.*)$", line)
            if m:
                k, v = m.group(1), m.group(2).strip().strip('"').strip("'")
                item[k] = v
        findings.append(item)
    return findings


def compute_handoff_digests(
    case_id: str,
    open_finding_ids: list[str],
    cycle: int,
    case_revision: str = "",
) -> dict[str, str]:
    """Handoff鮮度用の分離digestを正本入力から再計算する。"""
    return handoff_digests(case_id, open_finding_ids, cycle, case_revision)


def classify_evidence_ref(value: str) -> str:
    """Evidence 参照を absolute / file-uri / relative-path / prose に分類する。"""
    s = str(value).strip()
    if s.startswith("file://"):
        return "file-uri"
    if s.startswith("/") or (len(s) >= 3 and s[1] == ":" and s[2] in "/\\"):
        return "absolute"
    if " " in s or "\t" in s:
        return "prose"
    if "/" in s or s.startswith("./") or s.startswith("../"):
        return "relative-path"
    if re.match(r"^[\w.-]+\.[A-Za-z0-9]+$", s):
        return "relative-path"
    return "prose"


def resolve_in_workspace(path_str: str, workspace_root: Path) -> Path:
    """相対パスを workspace_root 配下に解決する。絶対パス・file://・配下脱出は拒否。"""
    raw = str(path_str).strip()
    if raw.startswith("file://"):
        raise ValueError("Verification failed: file:// references are not accepted")
    p = Path(raw)
    if p.is_absolute():
        raise ValueError(
            "Verification failed: path must be workspace-relative; absolute paths are not accepted"
        )
    root = workspace_root.resolve()
    candidate = (root / p).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"Verification failed: path '{path_str}' is outside the workspace"
        ) from exc
    return candidate


def path_exists_for_verify(path_str: str, workspace_root: Path) -> bool:
    try:
        return resolve_in_workspace(path_str, workspace_root).exists()
    except ValueError:
        return False


def require_workspace_existing_path(path_str: str, workspace_root: Path, label: str) -> None:
    try:
        target = resolve_in_workspace(path_str, workspace_root)
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("Verification failed: path "):
            raise ValueError(msg.replace("path ", f"{label} ", 1)) from exc
        raise
    if not target.exists():
        raise ValueError(f"Verification failed: {label} '{path_str}' does not exist")


class ReviewerLifecycle:
    def __init__(
        self,
        qa_root: str = "docs/ADR/QA",
        role: str = "reviewer",
        workspace_root: Optional[str] = None,
    ):
        self.qa_root = Path(qa_root)
        self.role = role
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        if self.role != "reviewer":
            raise PermissionError(f"ReviewerLifecycle requires role 'reviewer', got '{role}'")

    def _case_dir(self, case_id: str) -> Path:
        return self.qa_root / case_id

    def init_case(
        self,
        case_id: str,
        target: str,
        purpose: str,
        profile: str = "standard",
        title: str = "QA Review Case",
    ) -> dict[str, Any]:
        if not case_id or not re.match(r"^QA-[0-9]{4}(-[a-z0-9-]+)?$", case_id):
            raise ValueError(f"Invalid case_id format: '{case_id}'")
        if not target or not target.strip():
            raise ValueError("Target file or directory path is required")
        if not purpose or not purpose.strip():
            raise ValueError("Purpose document or statement is required")
        if profile not in VALID_PROFILES:
            raise ValueError(f"Invalid profile '{profile}'. Allowed: {sorted(VALID_PROFILES)}")

        case_path = self._case_dir(case_id)
        if case_path.exists():
            raise FileExistsError(f"Case directory already exists: {case_path}")

        # Check permissions
        check_write_permission(f"{case_path}/review.md", self.role)

        case_path.mkdir(parents=True, exist_ok=True)
        (case_path / "cycles").mkdir(exist_ok=True)
        (case_path / "evidence").mkdir(exist_ok=True)

        now = get_timestamp()
        # review.md
        review_content = (
            f"---\n"
            f"case_id: {case_id}\n"
            f"title: {title}\n"
            f"target: {target}\n"
            f"purpose: {purpose}\n"
            f"profile: {profile}\n"
            f"status: initialized\n"
            f"cycle: 1\n"
            f"created_at: {now}\n"
            f"updated_at: {now}\n"
            f"---\n"
            f"# {case_id}: {title}\n\n"
            f"## Status Summary\n"
            f"- State: initialized\n"
            f"- Profile: {profile}\n"
            f"- Target: `{target}`\n"
            f"- Purpose: `{purpose}`\n\n"
            f"## Open Findings\nNone\n"
        )
        (case_path / "review.md").write_text(review_content, encoding="utf-8")

        # findings.yaml
        findings_content = f"case_id: {case_id}\nprofile: {profile}\nfindings: []\n"
        (case_path / "findings.yaml").write_text(findings_content, encoding="utf-8")

        # traceability.yaml
        trace_content = f"case_id: {case_id}\ntarget: {target}\ntraceability: []\n"
        (case_path / "traceability.yaml").write_text(trace_content, encoding="utf-8")

        # events.jsonl
        init_event = {
            "timestamp": now,
            "case_id": case_id,
            "role": self.role,
            "action": "init",
            "status": "initialized",
            "target": target,
            "profile": profile,
        }
        (case_path / "events.jsonl").write_text(json.dumps(init_event) + "\n", encoding="utf-8")

        return {
            "status": "success",
            "case_id": case_id,
            "action": "init",
            "case_dir": str(case_path),
        }

    def record_findings(
        self,
        case_id: str,
        findings: list[dict[str, Any]],
        cycle: int = 1,
    ) -> dict[str, Any]:
        case_path = self._case_dir(case_id)
        if not case_path.exists():
            raise FileNotFoundError(f"Case directory not found: {case_path}")

        # Validate findings
        seen_ids = set()
        for f in findings:
            fid = f.get("id")
            if not fid or fid in seen_ids:
                raise ValueError(f"Finding ID missing or duplicate: '{fid}'")
            seen_ids.add(fid)

            cat = f.get("category")
            if not cat:
                raise ValueError(f"Finding '{fid}' missing category")

            sev = str(f.get("severity", "")).lower()
            if sev not in VALID_SEVERITIES:
                raise ValueError(f"Finding '{fid}' invalid severity '{sev}'")

            cls = f.get("purpose_classification")
            if cls not in VALID_PURPOSE_CLASSIFICATIONS:
                raise ValueError(
                    f"Finding '{fid}' missing or invalid purpose_classification '{cls}'. "
                    f"Allowed: {sorted(VALID_PURPOSE_CLASSIFICATIONS)}"
                )

            ev = f.get("evidence")
            if not ev:
                raise ValueError(f"Finding '{fid}' missing evidence references")

        # Write to findings.yaml and cycle report
        check_write_permission(f"{case_path}/findings.yaml", self.role)
        check_write_permission(f"{case_path}/traceability.yaml", self.role)
        check_write_permission(f"{case_path}/cycles/cycle-01-independent-review.md", self.role)

        now = get_timestamp()
        # Render simple YAML-like findings
        f_lines = [f"case_id: {case_id}", f"cycle: {cycle}", "findings:"]
        for f in findings:
            f_lines.extend([
                f"  - id: {f['id']}",
                f"    title: \"{f.get('title', '')}\"",
                f"    category: {f['category']}",
                f"    severity: {f['severity']}",
                f"    purpose_classification: {f['purpose_classification']}",
                f"    evidence: \"{f['evidence']}\"",
                f"    status: open",
            ])
        (case_path / "findings.yaml").write_text("\n".join(f_lines) + "\n", encoding="utf-8")

        # Update traceability.yaml
        t_lines = [f"case_id: {case_id}", "traceability:"]
        for f in findings:
            t_lines.extend([
                f"  - finding_id: {f['id']}",
                f"    classification: {f['purpose_classification']}",
                f"    evidence: \"{f['evidence']}\"",
                f"    status: open",
            ])
        (case_path / "traceability.yaml").write_text("\n".join(t_lines) + "\n", encoding="utf-8")

        # Record independent review cycle file
        cycle_file = case_path / "cycles" / f"cycle-{cycle:02d}-independent-review.md"
        cycle_content = (
            f"# Cycle {cycle:02d} Independent Review\n\n"
            f"- Case ID: {case_id}\n"
            f"- Date: {now}\n"
            f"- Reviewer: {self.role}\n\n"
            f"## Findings\n"
        )
        for f in findings:
            cycle_content += f"\n### [{f['id']}] {f.get('title', '')}\n- Severity: {f['severity']}\n- Classification: {f['purpose_classification']}\n- Evidence: {f['evidence']}\n"
        cycle_file.write_text(cycle_content, encoding="utf-8")

        # Append event
        event = {
            "timestamp": now,
            "case_id": case_id,
            "role": self.role,
            "action": "review",
            "cycle": cycle,
            "findings_count": len(findings),
            "status": "reviewed",
        }
        with open(case_path / "events.jsonl", "a", encoding="utf-8") as fp:
            fp.write(json.dumps(event) + "\n")

        return {
            "status": "success",
            "case_id": case_id,
            "action": "review",
            "findings_count": len(findings),
        }

    def render_handoff(
        self,
        case_id: str,
        cycle: int = 1,
        case_revision: str = "rev-001",
    ) -> dict[str, Any]:
        case_path = self._case_dir(case_id)
        if not case_path.exists():
            raise FileNotFoundError(f"Case directory not found: {case_path}")

        # Read findings
        findings_raw = (case_path / "findings.yaml").read_text(encoding="utf-8")
        open_finding_ids = [f["id"] for f in parse_findings_list(findings_raw) if f.get("status") == "open"]

        now = get_timestamp()
        digests = compute_handoff_digests(case_id, open_finding_ids, cycle, case_revision)
        digest_val = digests["content_digest"]

        handoff_content = (
            f"# QA Review Handoff Contract\n\n"
            f"- schema_version: \"1.2\"\n"
            f"- digest_version: \"v1\"\n"
            f"- case_id: {case_id}\n"
            f"- cycle: {cycle}\n"
            f"- case_revision: {case_revision}\n"
            f"- content_digest: {digests['content_digest']}\n"
            f"- semantic_digest: {digests['semantic_digest']}\n"
            f"- created_at: {now}\n"
            f"- origin_role: reviewer\n"
            f"- implementation_permission: scoped\n"
            f"- open_finding_ids: {json.dumps(open_finding_ids)}\n\n"
            f"## Active Open Findings\n"
        )
        for fid in open_finding_ids:
            handoff_content += f"\n- `{fid}`: Awaiting author response or fix submission."
        handoff_content += "\n"

        check_write_permission(f"{case_path}/handoff.md", self.role)
        (case_path / "handoff.md").write_text(handoff_content, encoding="utf-8")

        # Append event
        event = {
            "timestamp": now,
            "case_id": case_id,
            "role": self.role,
            "action": "handoff",
            "cycle": cycle,
            "digest": digest_val,
            "open_findings": open_finding_ids,
        }
        with open(case_path / "events.jsonl", "a", encoding="utf-8") as fp:
            fp.write(json.dumps(event) + "\n")

        return {
            "status": "success",
            "case_id": case_id,
            "action": "handoff",
            "digest": digest_val,
            "open_findings": open_finding_ids,
        }

    def verify_submission(
        self,
        case_id: str,
        submission: dict[str, Any],
        cycle: int = 1,
    ) -> dict[str, Any]:
        case_path = self._case_dir(case_id)
        if not case_path.exists():
            raise FileNotFoundError(f"Case directory not found: {case_path}")

        # Check cycle limit first
        review_text = (case_path / "review.md").read_text(encoding="utf-8")
        profile_match = re.search(r"profile:\s*([a-z-]+)", review_text)
        profile = profile_match.group(1) if profile_match else "standard"
        limit = PROFILE_CYCLE_LIMITS.get(profile, 2)

        # Rule: Author cannot self-close or set fixed-and-verified directly
        claimed_status = str(submission.get("status", "")).lower()
        if claimed_status in {"closed", "fixed-and-verified", "accepted"}:
            raise ValueError(
                f"Protocol violation: Author submission attempted to set terminal/verified status '{claimed_status}'. "
                "Author cannot self-close or self-verify findings."
            )

        # Rule: Unknown finding IDs are rejected
        findings_raw = (case_path / "findings.yaml").read_text(encoding="utf-8")
        findings_list = parse_findings_list(findings_raw)
        valid_open_ids = {f["id"] for f in findings_list if f.get("status") == "open"}
        sub_fids = set(submission.get("finding_ids", []))
        if not sub_fids:
            raise ValueError("Verification failed: Submission must specify at least one finding_id")
        
        unknown_ids = sub_fids - valid_open_ids
        if unknown_ids:
            raise ValueError(f"Protocol violation: Submission contains unknown Finding IDs: {sorted(unknown_ids)}")

        # Verification of handoff contract and revisions
        handoff_path = case_path / "handoff.md"
        if not handoff_path.exists():
            raise ValueError("Verification failed: handoff.md is required before verifying author submission")
        
        h_text = handoff_path.read_text(encoding="utf-8")

        # Stale digest: recompute with the same inputs as render_handoff
        # (use handoff-recorded cycle so verify cycle-limit checks stay independent)
        open_ids_for_digest = [f["id"] for f in findings_list if f.get("status") == "open"]
        handoff_cycle_m = re.search(r"(?m)^- cycle:\s*(\d+)", h_text)
        digest_cycle = int(handoff_cycle_m.group(1)) if handoff_cycle_m else cycle
        rev_match = re.search(r"case_revision:\s*([A-Za-z0-9_-]+)", h_text)
        expected_rev = rev_match.group(1) if rev_match else ""
        expected = compute_handoff_digests(case_id, open_ids_for_digest, digest_cycle, expected_rev)
        handoff_content_digest = ""
        handoff_semantic_digest = ""
        cm = re.search(r"content_digest:\s*(\S+)", h_text)
        sm = re.search(r"semantic_digest:\s*(\S+)", h_text)
        if cm:
            handoff_content_digest = cm.group(1).strip()
        if sm:
            handoff_semantic_digest = sm.group(1).strip()
        if handoff_semantic_digest != expected["semantic_digest"]:
            raise ValueError(
                "Verification failed: handoff semantic_digest is stale; regenerate handoff from canonical state"
            )
        if handoff_content_digest != expected["content_digest"]:
            raise ValueError(
                "Verification failed: handoff content_digest is stale; regenerate handoff from canonical state"
            )
        if compute_handoff_content_digest(h_text) != handoff_content_digest:
            raise ValueError(
                "Verification failed: handoff content_digest does not match handoff content"
            )

        sub_base_rev = submission.get("base_revision")
        if not sub_base_rev:
            raise ValueError("Verification failed: Submission lacks required base_revision")
        if expected_rev and sub_base_rev != expected_rev:
            raise ValueError(f"Revision conflict: Submission base_revision '{sub_base_rev}' does not match handoff '{expected_rev}'")

        # Test evidence check
        test_ev = submission.get("test_evidence")
        if not test_ev or not str(test_ev).strip():
            raise ValueError("Verification failed: Submission lacks concrete test evidence")
        ev_kind = classify_evidence_ref(str(test_ev))
        if ev_kind in {"absolute", "file-uri"}:
            raise ValueError(
                "Verification failed: Evidence must use repository-relative paths; "
                f"absolute or file:// references are not accepted ({ev_kind})"
            )
        if ev_kind == "relative-path":
            require_workspace_existing_path(str(test_ev).strip(), self.workspace_root, "test_evidence")

        # modified_files: required for technical fix submissions; all paths must exist
        disposition = str(submission.get("disposition") or "").lower()
        doc_only = disposition in {"doc-only", "documentation-only"}
        if "modified_files" not in submission:
            mod_files = None
        else:
            mod_files = submission.get("modified_files")
        if not doc_only:
            if mod_files is None or not isinstance(mod_files, list) or len(mod_files) == 0:
                raise ValueError(
                    "Verification failed: fix submission requires non-empty modified_files"
                )
            for mf in mod_files:
                require_workspace_existing_path(str(mf), self.workspace_root, "Modified file")
        elif mod_files:
            for mf in mod_files:
                require_workspace_existing_path(str(mf), self.workspace_root, "Modified file")

        if cycle > limit:
            # Transition to adjudication-required
            now = get_timestamp()
            event = {
                "timestamp": now,
                "case_id": case_id,
                "role": self.role,
                "action": "verify",
                "cycle": cycle,
                "outcome": "adjudication-required",
                "reason": f"Cycle limit {limit} exceeded for profile '{profile}'",
            }
            with open(case_path / "events.jsonl", "a", encoding="utf-8") as fp:
                fp.write(json.dumps(event) + "\n")
            return {
                "status": "adjudication-required",
                "case_id": case_id,
                "cycle": cycle,
                "reason": f"Cycle limit {limit} exceeded",
            }

        # Update findings.yaml to mark verified findings as verified
        check_write_permission(f"{case_path}/findings.yaml", self.role)
        updated_findings_text = findings_raw
        for fid in sub_fids:
            pattern = re.compile(rf"(  - id: {re.escape(fid)}.*?    status: )open", re.DOTALL)
            updated_findings_text = pattern.sub(r"\g<1>verified", updated_findings_text)
        (case_path / "findings.yaml").write_text(updated_findings_text, encoding="utf-8")

        # Record verification cycle
        now = get_timestamp()
        check_write_permission(f"{case_path}/cycles/cycle-{cycle:02d}-verification.md", self.role)
        ver_file = case_path / "cycles" / f"cycle-{cycle:02d}-verification.md"
        ver_content = (
            f"# Cycle {cycle:02d} Reviewer Verification\n\n"
            f"- Case ID: {case_id}\n"
            f"- Verified At: {now}\n"
            f"- Verified Findings: {sorted(sub_fids)}\n"
            f"- Outcome: fixed-and-verified\n"
        )
        ver_file.write_text(ver_content, encoding="utf-8")

        # Append event
        event = {
            "timestamp": now,
            "case_id": case_id,
            "role": self.role,
            "action": "verify",
            "cycle": cycle,
            "outcome": "verified",
            "verified_findings": sorted(sub_fids),
        }
        with open(case_path / "events.jsonl", "a", encoding="utf-8") as fp:
            fp.write(json.dumps(event) + "\n")

        return {
            "status": "success",
            "case_id": case_id,
            "action": "verify",
            "outcome": "verified",
        }

    def close_case(
        self,
        case_id: str,
        terminal_status: str,
        rationale: str = "",
    ) -> dict[str, Any]:
        case_path = self._case_dir(case_id)
        if not case_path.exists():
            raise FileNotFoundError(f"Case directory not found: {case_path}")

        if terminal_status not in VALID_TERMINAL_STATUSES:
            raise ValueError(f"Invalid terminal status '{terminal_status}'. Allowed: {sorted(VALID_TERMINAL_STATUSES)}")

        # Automatic Case Invariant Scans: REQUIRED markers in review.md
        review_text = (case_path / "review.md").read_text(encoding="utf-8")
        unresolved_markers = re.findall(r"REQUIRED:[A-Z0-9_:-]+", review_text)
        if unresolved_markers:
            raise ValueError(f"Cannot close case with unresolved REQUIRED markers in review.md: {unresolved_markers}")

        # Scan findings.yaml for open critical findings and validate risk-accepted metadata
        findings_raw = (case_path / "findings.yaml").read_text(encoding="utf-8")
        findings_list = parse_findings_list(findings_raw)
        
        open_critical = [f["id"] for f in findings_list if f.get("severity") == "critical" and f.get("status") == "open"]
        if open_critical:
            raise ValueError(f"Cannot close case with unresolved Critical findings in findings.yaml: {open_critical}")

        # Validate 5-element metadata for risk-accepted High findings
        for f in findings_list:
            if f.get("severity") == "high" and f.get("status") == "risk-accepted":
                required_elements = ["owner", "rationale", "scope_or_assumptions", "compensating_controls", "expiry_or_review_trigger"]
                missing = [el for el in required_elements if not f.get(el)]
                if missing:
                    raise ValueError(f"Cannot close case: High finding '{f['id']}' risk-accepted is missing required metadata: {missing}")

        now = get_timestamp()
        check_write_permission(f"{case_path}/review.md", self.role)

        # Update review.md status
        rev_text = re.sub(r"status:\s*[a-z-]+", f"status: {terminal_status}", review_text)
        rev_text += f"\n\n## Closure Decision\n- Terminal Status: `{terminal_status}`\n- Closed At: {now}\n- Rationale: {rationale}\n"
        (case_path / "review.md").write_text(rev_text, encoding="utf-8")

        # Append closure event
        event = {
            "timestamp": now,
            "case_id": case_id,
            "role": self.role,
            "action": "close",
            "terminal_status": terminal_status,
            "rationale": rationale,
        }
        with open(case_path / "events.jsonl", "a", encoding="utf-8") as fp:
            fp.write(json.dumps(event) + "\n")

        return {
            "status": "success",
            "case_id": case_id,
            "action": "close",
            "terminal_status": terminal_status,
        }
