"""Author提出の構造検証、境界検証、保存を行う。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .shared_core_adapter import load_digest_version_validator, load_handoff_content_digest, load_handoff_digests, load_shared_core

VALID_DISPOSITIONS = {
    "accepted",
    "fix-submitted",
    "rejected-with-evidence",
    "deferred",
    "risk-accepted",
    "not-applicable",
}
FORBIDDEN_DISPOSITIONS = {"closed", "fixed-and-verified"}
REVIEWER_OWNED_KEYS = {
    "finding", "severity", "verification", "events", "closure", "case_status",
    "terminal_result", "review", "handoff",
}
FINDING_ID_RE = re.compile(r"QA-[0-9]+-F[0-9]+")


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        return {}
    result: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line or line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def handoff_meta(handoff_text: str) -> dict[str, str]:
    meta = _frontmatter(handoff_text)
    for line in handoff_text.splitlines():
        match = re.match(r"^-\s+([a-z_]+):\s*(.*?)\s*$", line)
        if match and match.group(1) not in meta:
            meta[match.group(1)] = match.group(2).strip('"').strip("'")
    return meta


def handoff_finding_ids(handoff_text: str) -> set[str]:
    """構造化されたopen_finding_idsだけを読む。本文全文検索は許可しない。"""
    match = re.search(r"(?ms)^open_finding_ids:\s*\n((?:\s+-\s+QA-[0-9]+-F[0-9]+\s*\n?)+)", handoff_text)
    if match:
        return set(FINDING_ID_RE.findall(match.group(1)))
    inline = re.search(r"(?m)^\s*-?\s*open_finding_ids:\s*(\[[^\n]+\])", handoff_text)
    if inline:
        try:
            values = json.loads(inline.group(1))
        except json.JSONDecodeError:
            return set()
        return {value for value in values if isinstance(value, str) and FINDING_ID_RE.fullmatch(value)}
    return set()


def canonical_finding_ids(case_dir: Path) -> set[str]:
    """正本のうちReviewerが未解決として扱うFinding IDだけを返す。

    Reviewerのhandoff digestは ``status: open`` の集合から算出されるため、
    Author側も同じ集合をdigest入力および許可集合として使用する。
    """
    findings_path = case_dir / "findings.yaml"
    if not findings_path.is_file():
        raise ValueError(f"canonical findings.yaml is required: {findings_path}")
    text = findings_path.read_text(encoding="utf-8")
    finding_ids: set[str] = set()
    for block in re.split(r"(?m)^\s*- id:\s*", text)[1:]:
        lines = block.splitlines()
        if not lines:
            continue
        match = re.match(r"(QA-[0-9]+-F[0-9]+)\s*$", lines[0].strip())
        status = re.search(r"(?m)^\s{4}status:\s*([^\s#]+)", block)
        if match and status and status.group(1).strip('"\'') == "open":
            finding_ids.add(match.group(1))
    return finding_ids


def _walk_keys(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if key in REVIEWER_OWNED_KEYS:
                found.append(key_path)
            found.extend(_walk_keys(child, key_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_walk_keys(child, f"{prefix}[{index}]"))
    return found


def resolve_in_workspace(path_str: str, workspace_root: Path) -> Path:
    raw = str(path_str).strip()
    if raw.startswith("file://"):
        raise ValueError("path must be repository-relative; file:// is not accepted")
    path = Path(raw)
    if path.is_absolute():
        raise ValueError("path must be repository-relative; absolute paths are not accepted")
    root = workspace_root.resolve()
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path is outside workspace: {path_str}") from exc
    return resolved


def _path_like(value: str) -> bool:
    return "/" in value or value.startswith((".", "evidence", "test"))


def validate_submission(
    submission: dict[str, Any],
    handoff_text: str,
    workspace_root: Path,
    canonical_case_dir: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    meta = handoff_meta(handoff_text)
    try:
        load_digest_version_validator()(meta.get("digest_version", ""))
    except (RuntimeError, ValueError):
        errors.append("unsupported-digest-version")
    try:
        if canonical_case_dir is None:
            raise ValueError("canonical_case_dir is required")
        known_ids = canonical_finding_ids(canonical_case_dir)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
        known_ids = set()
    handoff_ids = handoff_finding_ids(handoff_text)
    submission_id = submission.get("submission_id")
    if not isinstance(submission_id, str) or not re.fullmatch(r"submission-[A-Za-z0-9_-]+", submission_id):
        errors.append("invalid submission_id")
    errors.extend(f"Reviewer-owned field cannot be changed: {key}" for key in _walk_keys(submission))

    if not submission.get("case_id") or meta.get("case_id") not in {None, str(submission.get("case_id"))}:
        errors.append("case_id does not match handoff")
    if not submission.get("contract_version"):
        errors.append("contract_version is required")
    if meta.get("contract_version") and str(submission.get("contract_version")) != meta["contract_version"]:
        errors.append("contract_version does not match handoff")
    if not submission.get("base_revision"):
        errors.append("base_revision is required")
    digest_pair: dict[str, str] | None = None
    try:
        digest_pair = load_handoff_digests()(
            str(meta.get("case_id", "")),
            sorted(known_ids),
            int(meta.get("cycle", 1)),
            str(meta.get("case_revision", "")),
        )
    except (RuntimeError, ValueError, TypeError):
        errors.append("shared core digest is unavailable")
    expected_semantic = meta.get("semantic_digest")
    expected_content = meta.get("content_digest")
    if submission.get("expected_semantic_digest") != expected_semantic:
        errors.append("semantic_digest does not match handoff")
    if submission.get("expected_content_digest") != expected_content:
        errors.append("content_digest does not match handoff")
    if expected_semantic and expected_semantic == expected_content:
        errors.append("legacy equivalent semantic/content digest is not accepted")
    if digest_pair and expected_semantic != digest_pair["semantic_digest"]:
        errors.append("handoff semantic_digest is stale")
    if digest_pair and expected_content != digest_pair["content_digest"]:
        errors.append("handoff content_digest is stale")
    if digest_pair:
        try:
            if load_handoff_content_digest()(handoff_text) != expected_content:
                errors.append("handoff content_digest does not match handoff content")
        except (RuntimeError, ValueError, TypeError):
            errors.append("handoff content digest is unavailable")
    if meta.get("case_revision") and str(submission.get("base_revision")) != str(meta["case_revision"]):
        errors.append("base_revision does not match handoff")

    responses = submission.get("responses")
    if not isinstance(responses, dict) or not responses:
        errors.append("responses must be a non-empty object")
        responses = {}
    unknown = sorted(set(responses) - known_ids)
    errors.extend(f"unknown Finding: {fid}" for fid in unknown)
    errors.extend(f"Finding is not listed in handoff: {fid}" for fid in sorted(set(responses) - handoff_ids))
    for finding_id, response in responses.items():
        if not isinstance(response, dict):
            errors.append(f"response must be an object: {finding_id}")
            continue
        disposition = response.get("disposition")
        if disposition in FORBIDDEN_DISPOSITIONS:
            errors.append(f"Author cannot self-close a Finding: {disposition}")
        elif disposition not in VALID_DISPOSITIONS:
            errors.append(f"invalid Disposition: {disposition}")
        if not str(response.get("justification", "")).strip():
            errors.append(f"justification is required: {finding_id}")
        if disposition == "fix-submitted" and not submission.get("result_revision"):
            errors.append("fix-submitted requires result_revision")

    evidence = submission.get("evidence", [])
    if not isinstance(evidence, list):
        errors.append("evidence must be a list")
        evidence = []
    for reference in evidence:
        if not isinstance(reference, str) or not reference.strip():
            errors.append("evidence references must be non-empty strings")
            continue
        if _path_like(reference):
            try:
                target = resolve_in_workspace(reference, workspace_root)
                if not target.exists():
                    errors.append(f"evidence does not exist: {reference}")
            except ValueError as exc:
                errors.append(str(exc))

    modified = submission.get("modified_files")
    needs_files = any(isinstance(r, dict) and r.get("disposition") == "fix-submitted" for r in responses.values())
    if needs_files and (not isinstance(modified, list) or not modified):
        errors.append("fix-submitted requires non-empty modified_files")
    if isinstance(modified, list):
        for item in modified:
            try:
                target = resolve_in_workspace(str(item), workspace_root)
                if not target.exists():
                    errors.append(f"modified file does not exist: {item}")
            except ValueError as exc:
                errors.append(str(exc))
    return errors


def write_submission(case_dir: Path, cycle: int, submission: dict[str, Any]) -> Path:
    destination = case_dir / "cycles" / f"cycle-{cycle:02d}-submission.json"
    if not author_write_path_allowed(destination, case_dir):
        raise PermissionError(f"Author write path is not allowed: {destination}")
    if destination.exists():
        raise FileExistsError(f"submission already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(submission, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def author_write_path_allowed(path: Path, case_dir: Path) -> bool:
    try:
        relative = path.resolve().relative_to(case_dir.resolve()).as_posix()
    except ValueError:
        return False
    return bool(re.fullmatch(r"cycles/cycle-[0-9]+-(author-response\.md|submission\.json)", relative))


def write_author_response(case_dir: Path, cycle: int, submission: dict[str, Any]) -> Path:
    destination = case_dir / "cycles" / f"cycle-{cycle:02d}-author-response.md"
    if not author_write_path_allowed(destination, case_dir):
        raise PermissionError(f"Author write path is not allowed: {destination}")
    if destination.exists():
        raise FileExistsError(f"author response already exists: {destination}")
    lines = [
        "# Author Response",
        "",
        f"- case_id: `{submission.get('case_id', '')}`",
        f"- submission_id: `{submission.get('submission_id', '')}`",
        f"- cycle: {cycle}",
        "- next_action: `reviewer-verification`",
        "",
    ]
    for finding_id, response in submission.get("responses", {}).items():
        lines.extend([
            f"## {finding_id}",
            "",
            f"- Disposition: `{response.get('disposition', '')}`",
            f"- Justification: {response.get('justification', '')}",
            "",
        ])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    return destination


def validate_and_save(
    case_dir: Path,
    handoff: Path,
    submission: dict[str, Any],
    cycle: int,
    workspace_root: Path,
) -> tuple[Path, Path]:
    handoff_text = handoff.read_text(encoding="utf-8")
    errors = validate_submission(submission, handoff_text, workspace_root, case_dir)
    if errors:
        raise ValueError("; ".join(errors))
    # Adapter load is deliberate: fail closed when the canonical shared core is unavailable.
    load_shared_core()
    return write_author_response(case_dir, cycle, submission), write_submission(case_dir, cycle, submission)
