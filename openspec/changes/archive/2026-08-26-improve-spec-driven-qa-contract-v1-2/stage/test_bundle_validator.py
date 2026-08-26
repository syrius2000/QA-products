import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from bundle_validator import validate_bundle


def test_stage_bundle_passes_all_required_gates():
    assert validate_bundle(ROOT) == []
