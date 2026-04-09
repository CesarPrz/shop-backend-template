import json
from decimal import Decimal

import pytest

from shop.shared.responses import error_response, json_response


def test_json_response_defaults():
    response = json_response(201, {"id": "abc"})

    assert response["statusCode"] == 201
    assert response["headers"] == {"Content-Type": "application/json"}
    assert json.loads(response["body"]) == {"id": "abc"}


def test_json_response_merges_headers():
    response = json_response(200, {}, headers={"Cache-Control": "no-store"})

    assert response["headers"]["Cache-Control"] == "no-store"
    assert response["headers"]["Content-Type"] == "application/json"


def test_json_response_serializes_decimals():
    body = json.loads(json_response(200, {"qty": Decimal("3"), "price": Decimal("9.99")})["body"])

    assert body == {"qty": 3, "price": 9.99}


def test_json_response_rejects_unknown_types():
    with pytest.raises(TypeError):
        json_response(200, {"value": object()})


def test_error_response():
    response = error_response(404, "Product not found", code="NOT_FOUND")

    assert response["statusCode"] == 404
    assert json.loads(response["body"]) == {
        "error": {"message": "Product not found", "code": "NOT_FOUND"}
    }


def test_error_response_without_code():
    body = json.loads(error_response(400, "Invalid payload")["body"])

    assert body == {"error": {"message": "Invalid payload"}}


def test_error_response_with_details():
    body = json.loads(
        error_response(400, "Invalid product payload", code="VALIDATION", details=["x"])["body"]
    )

    assert body["error"]["details"] == ["x"]
