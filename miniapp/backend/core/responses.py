from typing import Any, Dict, Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str


class SuccessResponse(BaseModel):
    data: Any
    error: Optional[ErrorDetail] = None


class ErrorResponse(BaseModel):
    data: Optional[Any] = None
    error: ErrorDetail


def success_response(data: Any) -> Dict[str, Any]:
    """Return the standard success envelope."""
    return {"data": data, "error": None}


def error_response(code: str, message: str) -> Dict[str, Any]:
    """Return the standard error envelope."""
    return {"data": None, "error": {"code": code, "message": message}}
