import base64
import json
from decimal import Decimal

import pytest

from shop.shared.validation import ValidationError, parse_json_body, validate_product

VALID_PRODUCT = {"name": "T-shirt", "price": 19.99, "stock": 10}


def test_parse_json_body(http_event):
    event = http_event("POST", "/products", body=json.dumps({"name": "Mug"}))

    assert parse_json_body(event) == {"name": "Mug"}


def test_parse_json_body_base64(http_event):
    event = http_event("POST", "/products", body=base64.b64encode(b'{"a": 1}').decode())
    event["isBase64Encoded"] = True

    assert parse_json_body(event) == {"a": 1}


@pytest.mark.parametrize(
    ("body", "code"),
    [
        (None, "INVALID_BODY"),
        ("", "INVALID_BODY"),
        ("{not json", "INVALID_JSON"),
        ("[1]", "INVALID_BODY"),
    ],
)
def test_parse_json_body_rejects_invalid(http_event, body, code):
    with pytest.raises(ValidationError) as exc:
        parse_json_body(http_event("POST", "/products", body=body))

    assert exc.value.code == code


def test_validate_product_cleans_fields():
    cleaned = validate_product({**VALID_PRODUCT, "name": "  T-shirt ", "category": "clothes"})

    assert cleaned == {
        "name": "T-shirt",
        "price": Decimal("19.99"),
        "stock": 10,
        "category": "clothes",
    }


def test_validate_product_requires_fields():
    with pytest.raises(ValidationError) as exc:
        validate_product({})

    assert exc.value.details == ["name is required", "price is required", "stock is required"]


def test_validate_product_rejects_unknown_fields():
    with pytest.raises(ValidationError) as exc:
        validate_product({**VALID_PRODUCT, "id": "abc"})

    assert exc.value.details == ["unknown field: id"]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("name", "", "name must not be empty"),
        ("name", 42, "name must be a string"),
        ("name", "x" * 121, "name must be at most 120 characters"),
        ("description", "x" * 1001, "description must be at most 1000 characters"),
        ("price", "9.99", "price must be a number"),
        ("price", True, "price must be a number"),
        ("price", float("nan"), "price must be a number"),
        ("price", -1, "price must be greater than or equal to 0"),
        ("price", 1000001, "price must be at most 1000000"),
        ("price", 9.999, "price must have at most 2 decimal places"),
        ("stock", 1.5, "stock must be an integer"),
        ("stock", False, "stock must be an integer"),
        ("stock", -3, "stock must be greater than or equal to 0"),
    ],
)
def test_validate_product_field_errors(field, value, message):
    with pytest.raises(ValidationError) as exc:
        validate_product({**VALID_PRODUCT, field: value})

    assert exc.value.details == [message]


def test_validate_product_partial():
    assert validate_product({"stock": 0}, partial=True) == {"stock": 0}


def test_validate_product_partial_requires_a_field():
    with pytest.raises(ValidationError) as exc:
        validate_product({}, partial=True)

    assert exc.value.details == ["at least one field must be provided"]
