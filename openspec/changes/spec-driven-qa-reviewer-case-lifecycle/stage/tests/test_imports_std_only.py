import ast
import sys
from pathlib import Path

STAGE_DIR = Path(__file__).resolve().parents[1]

# Python stdlib modules
STDLIB_MODULES = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else {
    "sys", "os", "json", "re", "pathlib", "datetime", "hashlib",
    "typing", "shutil", "importlib", "subprocess", "math", "collections",
    "functools", "itertools", "dataclasses", "enum", "abc", "contextlib",
    "__future__", "argparse", "unittest"
}

def test_reviewer_runtime_imports_only_stdlib():
    reviewer_dir = STAGE_DIR / "spec-driven-qa-review"
    for py_file in reviewer_dir.glob("**/*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    assert root_mod in STDLIB_MODULES or root_mod in {"shared_core", "spec_driven_qa_review"}, \
                        f"Non-standard import '{alias.name}' in {py_file}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    assert root_mod in STDLIB_MODULES or root_mod in {"shared_core", "spec_driven_qa_review"} or node.level > 0, \
                        f"Non-standard import '{node.module}' in {py_file}"
