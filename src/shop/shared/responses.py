"""Helpers to build API Gateway (HTTP API, payload v2) responses."""

import json
from decimal import Decimal
from typing import Any

DEFAULT_HEADERS = {"Content-Type": "application/json"}


def _default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def json_response(status_code: int, body: Any, headers: dict[str, str] | None = None) -> dict:
    return {
        "statusCode": status_code,
        "headers": {**DEFAULT_HEADERS, **(headers or {})},
        "body": json.dumps(body, default=_default),
    }


def error_response(
    status_code: int, message: str, code: str | None = None, details: list[str] | None = None
) -> dict:
    error: dict[str, Any] = {"message": message}
    if code:
        error["code"] = code
    if details:
        error["details"] = details
    return json_response(status_code, {"error": error})


def empty_response(status_code: int = 204) -> dict:
    return {"statusCode": status_code, "headers": {}, "body": ""}
