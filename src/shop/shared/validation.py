"""Request parsing and product payload validation."""

import base64
import binascii
import json
from decimal import Decimal
from typing import Any

NAME_MAX_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 1000
CATEGORY_MAX_LENGTH = 50
PRICE_MAX = Decimal("1000000")

REQUIRED_FIELDS = ("name", "price", "stock")
OPTIONAL_FIELDS = ("description", "category")
ALLOWED_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


class ValidationError(Exception):
    def __init__(self, message: str, details: list[str] | None = None, code: str = "VALIDATION"):
        super().__init__(message)
        self.message = message
        self.details = details or []
        self.code = code


def parse_json_body(event: dict) -> dict:
    """Decode the JSON object sent in an HTTP API event body."""
    raw = event.get("body")
    if not raw:
        raise ValidationError("Request body is required", code="INVALID_BODY")
    if event.get("isBase64Encoded"):
        try:
            raw = base64.b64decode(raw).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise ValidationError("Request body is not valid base64", code="INVALID_BODY") from exc
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError("Request body is not valid JSON", code="INVALID_JSON") from exc
    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object", code="INVALID_BODY")
    return body


def _validate_text(value: Any, field: str, max_length: int, *, required: bool) -> str | list[str]:
    if not isinstance(value, str):
        return [f"{field} must be a string"]
    value = value.strip()
    if required and not value:
        return [f"{field} must not be empty"]
    if len(value) > max_length:
        return [f"{field} must be at most {max_length} characters"]
    return value


def _validate_price(value: Any) -> Decimal | list[str]:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return ["price must be a number"]
    price = Decimal(str(value))
    if not price.is_finite():
        return ["price must be a number"]
    if price < 0:
        return ["price must be greater than or equal to 0"]
    if price > PRICE_MAX:
        return [f"price must be at most {PRICE_MAX}"]
    if price.as_tuple().exponent < -2:
        return ["price must have at most 2 decimal places"]
    return price


def _validate_stock(value: Any) -> int | list[str]:
    if isinstance(value, bool) or not isinstance(value, int):
        return ["stock must be an integer"]
    if value < 0:
        return ["stock must be greater than or equal to 0"]
    return value


VALIDATORS = {
    "name": lambda v: _validate_text(v, "name", NAME_MAX_LENGTH, required=True),
    "description": lambda v: _validate_text(
        v, "description", DESCRIPTION_MAX_LENGTH, required=False
    ),
    "category": lambda v: _validate_text(v, "category", CATEGORY_MAX_LENGTH, required=False),
    "price": _validate_price,
    "stock": _validate_stock,
}


def validate_product(payload: dict, *, partial: bool = False) -> dict:
    """Validate a product payload and return the cleaned fields.

    With ``partial=True`` (updates), required fields may be omitted but at least one
    field must be present.
    """
    errors = [f"unknown field: {field}" for field in sorted(set(payload) - set(ALLOWED_FIELDS))]

    if partial:
        if not errors and not payload:
            errors.append("at least one field must be provided")
    else:
        errors += [f"{field} is required" for field in REQUIRED_FIELDS if field not in payload]

    cleaned = {}
    for field in ALLOWED_FIELDS:
        if field not in payload:
            continue
        result = VALIDATORS[field](payload[field])
        if isinstance(result, list):
            errors += result
        else:
            cleaned[field] = result

    if errors:
        raise ValidationError("Invalid product payload", details=errors)
    return cleaned
