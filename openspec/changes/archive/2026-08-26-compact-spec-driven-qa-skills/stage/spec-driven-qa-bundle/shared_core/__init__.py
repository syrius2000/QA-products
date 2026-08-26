"""ステージングBundleの共有コア。標準ライブラリのみで動作する。"""

from .runtime import BundleError, authorize, load_request, run
from .authorization import allowed
from .contract import validate_contract
from .digest import content_digest
from .evidence import can_mark_fixed_and_verified, status_is_valid
from .links import classify_link, validate_link
from .secrets import contains_secret
from .state import can_transition
from .integration import verify_submission, verified_candidate
from .guards import content_digest_for_case, validate_handoff
from .compat import invoke_legacy, normalize_contract_version

__all__ = ["BundleError", "authorize", "load_request", "run", "allowed", "validate_contract", "content_digest", "can_mark_fixed_and_verified", "status_is_valid", "validate_link", "classify_link", "contains_secret", "can_transition", "verify_submission", "verified_candidate", "content_digest_for_case", "validate_handoff", "invoke_legacy", "normalize_contract_version"]
