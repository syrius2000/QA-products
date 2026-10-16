"""CLIの終了コードと例外。既存Skillに合わせ、0成功・2契約拒否・3入出力・4内部エラーとする。"""
from __future__ import annotations

EXIT_OK = 0
EXIT_CONTRACT = 2
EXIT_IO = 3
EXIT_INTERNAL = 4


class SpecReviewError(Exception):
    """利用者へ理由と次の操作を示す例外。"""

    def __init__(self, message: str, action: str = '', exit_code: int = EXIT_CONTRACT, details=None):
        super().__init__(message)
        self.message = message
        self.action = action
        self.exit_code = exit_code
        self.details = details or {}

    def as_result(self) -> dict:
        return {'status': 'error', 'message': self.message, 'action': self.action, 'details': self.details}


def contract(message: str, action: str = '', details=None) -> SpecReviewError:
    return SpecReviewError(message, action, EXIT_CONTRACT, details)


def io_error(message: str, action: str = '', details=None) -> SpecReviewError:
    return SpecReviewError(message, action, EXIT_IO, details)
