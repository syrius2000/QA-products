"""Author専用の薄いLauncher。Bundle外をimport対象にしない。"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    from shared_core.cli import main  # noqa: E402
except ModuleNotFoundError:
    import json
    print(json.dumps({"status": "error", "code": "shared_core_missing"}), file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main("author"))
