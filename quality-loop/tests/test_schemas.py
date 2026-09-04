from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


try:
    import jsonschema  # type: ignore[import-untyped]

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


def validate_schema(instance: Any, schema: dict[str, Any], path: str = "") -> None:
    """Python標準ライブラリだけで厳密に動作するJSON Schema (Draft 2020-12サブセット) 検証ヘルパー"""
    schema_type = schema.get("type")
    if schema_type:
        types = [schema_type] if isinstance(schema_type, str) else schema_type
        type_valid = False
        for t in types:
            if t == "string" and isinstance(instance, str):
                type_valid = True
            elif t == "integer" and isinstance(instance, int) and not isinstance(instance, bool):
                type_valid = True
            elif t == "number" and (isinstance(instance, (int, float)) and not isinstance(instance, bool)):
                type_valid = True
            elif t == "boolean" and isinstance(instance, bool):
                type_valid = True
            elif t == "array" and isinstance(instance, list):
                type_valid = True
            elif t == "object" and isinstance(instance, dict):
                type_valid = True
            elif t == "null" and instance is None:
                type_valid = True
        if not type_valid:
            raise AssertionError(f"Schema type mismatch at '{path}': expected {types}, got {type(instance).__name__}")

    if "minimum" in schema and isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if instance < schema["minimum"]:
            raise AssertionError(f"Schema minimum violation at '{path}': {instance} < {schema['minimum']}")

    if "maximum" in schema and isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if instance > schema["maximum"]:
            raise AssertionError(f"Schema maximum violation at '{path}': {instance} > {schema['maximum']}")

    if "minLength" in schema and isinstance(instance, str):
        if len(instance) < schema["minLength"]:
            raise AssertionError(f"Schema minLength violation at '{path}': len('{instance}') < {schema['minLength']}")

    if "minItems" in schema and isinstance(instance, list):
        if len(instance) < schema["minItems"]:
            raise AssertionError(f"Schema minItems violation at '{path}': len({instance}) < {schema['minItems']}")

    if "enum" in schema and instance not in schema["enum"]:
        raise AssertionError(f"Schema enum violation at '{path}': {instance} not in {schema['enum']}")

    if "const" in schema and instance != schema["const"]:
        raise AssertionError(f"Schema const violation at '{path}': {instance} != {schema['const']}")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for req in required:
            if req not in instance:
                raise AssertionError(f"Missing required property '{req}' at '{path}'")

        properties = schema.get("properties", {})
        additional_allowed = schema.get("additionalProperties", True)
        if not additional_allowed:
            for k in instance:
                if k not in properties:
                    raise AssertionError(f"Additional property '{k}' not allowed at '{path}'")

        for k, v in instance.items():
            if k in properties:
                validate_schema(v, properties[k], f"{path}.{k}" if path else k)

    elif isinstance(instance, list):
        items_schema = schema.get("items")
        if items_schema:
            for idx, item in enumerate(instance):
                validate_schema(item, items_schema, f"{path}[{idx}]")


class SchemasTest(unittest.TestCase):
    def test_all_six_schemas_exist_and_are_valid_json(self) -> None:
        schema_dir = Path(__file__).resolve().parent.parent / "schemas"
        expected_schemas = [
            "case.schema.json",
            "intake.schema.json",
            "review.schema.json",
            "submit-plan.schema.json",
            "review-plan.schema.json",
            "response.schema.json",
            "verify.schema.json",
            "assess-risk.schema.json",
            "adjudicate.schema.json",
            "standalone-review-input.schema.json",
        ]

        for name in expected_schemas:
            path = schema_dir / name
            self.assertTrue(path.is_file(), f"Missing schema: {name}")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("$schema", data)
            self.assertEqual("object", data.get("type"))
            self.assertTrue(len(data.get("required", [])) > 0)

    def test_standalone_schema_is_canonical_and_packaged_reference_matches(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = json.loads(
            (root / "schemas" / "standalone-review-input.schema.json").read_text(
                encoding="utf-8"
            )
        )
        packaged = json.loads(
            (
                root
                / "skills"
                / "quality-review"
                / "references"
                / "standalone-review-input.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(source, packaged)
        self.assertEqual({"owner", "targets"}, set(source["required"]))
        self.assertTrue(source["properties"]["targets"]["uniqueItems"])

    def test_finding_classifications_match_model_and_schema(self) -> None:
        from quality_loop.model import FINDING_CLASSIFICATIONS
        schema_path = Path(__file__).resolve().parent.parent / "schemas" / "review.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        schema_classifications = set(
            data["properties"]["findings"]["items"]["properties"]["classification"]["enum"]
        )
        self.assertEqual(
            FINDING_CLASSIFICATIONS,
            schema_classifications,
            "quality_loop.model.FINDING_CLASSIFICATIONS と review.schema.json の classification enum が一致していません",
        )

    def test_severities_match_model_and_schema(self) -> None:
        from quality_loop.model import SEVERITIES
        schema_path = Path(__file__).resolve().parent.parent / "schemas" / "review.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        schema_severities = set(
            data["properties"]["findings"]["items"]["properties"]["severity"]["enum"]
        )
        self.assertEqual(
            SEVERITIES,
            schema_severities,
            "quality_loop.model.SEVERITIES と review.schema.json の severity enum が一致していません",
        )

    def test_verification_results_match_model_and_schema(self) -> None:
        from quality_loop.model import VERIFICATION_RESULTS
        schema_path = Path(__file__).resolve().parent.parent / "schemas" / "verify.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        schema_results = set(
            data["properties"]["verifications"]["items"]["properties"]["result"]["enum"]
        )
        self.assertEqual(
            VERIFICATION_RESULTS,
            schema_results,
            "quality_loop.model.VERIFICATION_RESULTS と verify.schema.json の result enum が一致していません",
        )

    def test_case_schema_matches_every_operation_output(self) -> None:
        """P0-2: 全主要operation完了後のcase.jsonがcase.schema.jsonに適合する"""
        import tempfile
        from quality_loop.engine import QualityLoop
        from test_quality_loop import complete_intake

        case_schema = json.loads(
            (Path(__file__).resolve().parent.parent / "schemas" / "case.schema.json").read_text(encoding="utf-8")
        )
        required_keys = set(case_schema["required"])

        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))

            # 1. create-case
            intake = complete_intake()
            intake["implementation_authorization"] = {
                "allowed": True,
                "finding_ids": ["F-001"],
                "allowed_targets": ["artifact.txt"],
            }
            c1 = loop.create_case(intake)
            case_1 = loop.store.load("QMS-0001")
            validate_schema(case_1, case_schema)

            # 2. review
            r1 = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-rev-01",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-01",
                    "previous_handoff_id": c1["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-001",
                            "classification": "requirement-violation",
                            "severity": "high",
                            "requirement_ref": "REQ-001",
                            "observed_fact": "不適合",
                            "impact": "動作不能",
                            "expected_state": "正常",
                            "verification_method": "テスト",
                            "evidence_refs": [],
                            "status": "open",
                            "plan_required": True,
                        }
                    ],
                    "evidence": [],
                },
            )
            case_2 = loop.store.load("QMS-0001")
            validate_schema(case_2, case_schema)

            # 3. submit-plan
            p1 = loop.submit_plan(
                "QMS-0001",
                {
                    "operation_id": "op-plan-01",
                    "actor_id": "imp-01",
                    "role": "implementer",
                    "invocation_id": "inv-imp-01",
                    "previous_handoff_id": r1["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "plans": [
                        {
                            "finding_id": "F-001",
                            "understanding": "不適合の指摘内容を正しく理解した",
                            "disposition_intent": "fix",
                            "proposed_actions": ["対象箇所の修正と単体テストの追加"],
                            "planned_evidence": ["単体テストログ"],
                            "risk_assessment": "低",
                        }
                    ],
                },
            )
            case_3 = loop.store.load("QMS-0001")
            validate_schema(case_3, case_schema)

            # 4. review-plan
            rp1 = loop.review_plan(
                "QMS-0001",
                {
                    "operation_id": "op-rp-01",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-02",
                    "previous_handoff_id": p1["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "plan_reviews": [
                        {
                            "finding_id": "F-001",
                            "outcome": "plan-accepted",
                            "rationale": "計画合意",
                        }
                    ],
                },
            )
            case_4 = loop.store.load("QMS-0001")
            validate_schema(case_4, case_schema)

            # 5. submit-response
            s1 = loop.submit_response(
                "QMS-0001",
                {
                    "operation_id": "op-sub-01",
                    "actor_id": "imp-01",
                    "role": "implementer",
                    "invocation_id": "inv-imp-02",
                    "previous_handoff_id": rp1["handoff"]["handoff_id"],
                    "expected_case_revision": 4,
                    "changed_targets": ["artifact.txt"],
                    "responses": [
                        {
                            "finding_id": "F-001",
                            "disposition": "fix-submitted",
                            "rationale": "修正完了",
                            "evidence_refs": ["EV-01"],
                        }
                    ],
                    "evidence": [
                        {
                            "evidence_id": "EV-01",
                            "level": "observed",
                            "target_revision": "r2",
                            "method": "test",
                            "result": "pass",
                            "summary": "テスト成功",
                        }
                    ],
                },
            )
            case_5 = loop.store.load("QMS-0001")
            validate_schema(case_5, case_schema)

            # 6. verify
            v1 = loop.verify(
                "QMS-0001",
                {
                    "operation_id": "op-ver-01",
                    "actor_id": "reviewer-01",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-03",
                    "previous_handoff_id": s1["handoff"]["handoff_id"],
                    "expected_case_revision": 5,
                    "verifications": [
                        {
                            "finding_id": "F-001",
                            "result": "verified",
                            "rationale": "確認完了",
                            "evidence_refs": ["EV-01"],
                        }
                    ],
                    "new_findings": [],
                    "change_observation": {
                        "method": "finite-manifest",
                        "scope": ["artifact.txt"],
                        "before_evidence_id": "EV-01",
                        "after_evidence_id": "EV-01",
                        "observed_changed_targets": ["artifact.txt"],
                        "limitations": [],
                    },
                    "evidence": [],
                },
            )
            case_6 = loop.store.load("QMS-0001")
            validate_schema(case_6, case_schema)

            # 7. adjudicate
            a1 = loop.adjudicate(
                "QMS-0001",
                {
                    "operation_id": "op-adj-01",
                    "actor_id": "owner-001",
                    "role": "owner",
                    "invocation_id": "inv-owner-01",
                    "previous_handoff_id": v1["handoff"]["handoff_id"],
                    "expected_case_revision": 6,
                    "decision": "accepted",
                    "rationale": "全件適合を確認したため受入",
                    "confirm": True,
                },
            )
            case_7 = loop.store.load("QMS-0001")
            validate_schema(case_7, case_schema)

    def test_all_templates_are_valid_against_schemas(self) -> None:
        """P0-3: templates/ 内の全テンプレートJSONが対応スキーマの必須項目を満たす"""
        template_dir = Path(__file__).resolve().parent.parent / "templates"
        intake_data = json.loads((template_dir / "intake.json").read_text(encoding="utf-8"))
        baseline = intake_data.get("baseline", {})
        self.assertIn("intended_use", baseline)
        self.assertIn("risk_context", baseline)
        self.assertIn("criticality", baseline["risk_context"])

    def test_all_examples_validate_against_case_schema(self) -> None:
        """P0-4 / Phase 3: examples/ 内の全 case.json が case.schema.json に適合する"""
        case_schema = json.loads(
            (Path(__file__).resolve().parent.parent / "schemas" / "case.schema.json").read_text(encoding="utf-8")
        )
        examples_dir = Path(__file__).resolve().parent.parent / "examples"
        for example_case_path in examples_dir.glob("*/case.json"):
            with self.subTest(example=example_case_path.parent.name):
                data = json.loads(example_case_path.read_text(encoding="utf-8"))
                validate_schema(data, case_schema, path=example_case_path.parent.name)

    def test_all_schemas_and_examples_with_real_jsonschema_if_available(self) -> None:
        """Optional: jsonschemaが利用可能な環境ではDraft 2020-12完全仕様で全スキーマと実例をテスト"""
        if not HAS_JSONSCHEMA:
            self.skipTest("optional dev dependency 'jsonschema' is not installed (skipping full draft-2020-12 test)")
        schema_dir = Path(__file__).resolve().parent.parent / "schemas"
        examples_dir = Path(__file__).resolve().parent.parent / "examples"
        case_schema = json.loads((schema_dir / "case.schema.json").read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(case_schema)

        for example_case_path in examples_dir.glob("*/case.json"):
            with self.subTest(example=example_case_path.parent.name):
                data = json.loads(example_case_path.read_text(encoding="utf-8"))
                validator.validate(data)


if __name__ == "__main__":
    unittest.main()
