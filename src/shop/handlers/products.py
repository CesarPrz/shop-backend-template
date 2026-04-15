"""Product catalogue endpoints: /products and /products/{productId}."""

import base64
import binascii
import json

from shop.products import repository
from shop.shared.responses import empty_response, error_response, json_response
from shop.shared.validation import ValidationError, parse_json_body, validate_product

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def _not_found(product_id: str) -> dict:
    return error_response(404, f"Product {product_id} not found", code="NOT_FOUND")


def _invalid(exc: ValidationError) -> dict:
    return error_response(400, exc.message, code=exc.code, details=exc.details)


def _product_id(event: dict) -> str:
    return (event.get("pathParameters") or {}).get("productId", "")


def _encode_cursor(key: dict | None) -> str | None:
    if not key:
        return None
    return base64.urlsafe_b64encode(json.dumps(key).encode()).decode()


def _decode_cursor(cursor: str) -> dict | None:
    try:
        key = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return None
    if not isinstance(key, dict) or not isinstance(key.get("id"), str) or len(key) != 1:
        return None
    return key


def list_products(event, context):
    query = event.get("queryStringParameters") or {}

    limit = query.get("limit", str(DEFAULT_PAGE_SIZE))
    if not limit.isdigit() or not 1 <= int(limit) <= MAX_PAGE_SIZE:
        return error_response(
            400, f"limit must be an integer between 1 and {MAX_PAGE_SIZE}", code="VALIDATION"
        )

    start_key = None
    if "cursor" in query:
        start_key = _decode_cursor(query["cursor"])
        if start_key is None:
            return error_response(400, "cursor is invalid", code="VALIDATION")

    items, last_key = repository.list_products(int(limit), start_key)
    return json_response(200, {"items": items, "nextCursor": _encode_cursor(last_key)})


def get_product(event, context):
    product_id = _product_id(event)
    product = repository.get_product(product_id)
    if product is None:
        return _not_found(product_id)
    return json_response(200, product)


def create_product(event, context):
    try:
        fields = validate_product(parse_json_body(event))
    except ValidationError as exc:
        return _invalid(exc)

    product = repository.create_product(fields)
    return json_response(201, product, headers={"Location": f"/products/{product['id']}"})


def update_product(event, context):
    product_id = _product_id(event)
    try:
        fields = validate_product(parse_json_body(event), partial=True)
    except ValidationError as exc:
        return _invalid(exc)

    product = repository.update_product(product_id, fields)
    if product is None:
        return _not_found(product_id)
    return json_response(200, product)


def delete_product(event, context):
    product_id = _product_id(event)
    if not repository.delete_product(product_id):
        return _not_found(product_id)
    return empty_response(204)
