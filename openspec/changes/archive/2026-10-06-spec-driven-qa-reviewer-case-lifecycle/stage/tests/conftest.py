import sys
import importlib.util
from pathlib import Path

STAGE_DIR = Path(__file__).resolve().parents[1]

# Add stage dir to sys.path
if str(STAGE_DIR) not in sys.path:
    sys.path.insert(0, str(STAGE_DIR))

# Alias spec-driven-qa-review to spec_driven_qa_review in sys.modules
reviewer_pkg_dir = STAGE_DIR / "spec-driven-qa-review"
if reviewer_pkg_dir.exists():
    spec = importlib.util.spec_from_file_location("spec_driven_qa_review", str(reviewer_pkg_dir / "__init__.py"))
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        sys.modules["spec_driven_qa_review"] = mod
        mod.__path__ = [str(reviewer_pkg_dir)]
        spec.loader.exec_module(mod)
