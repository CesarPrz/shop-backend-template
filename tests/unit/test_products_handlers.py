import json

import pytest

from shop.handlers import products

VALID_PRODUCT = {"name": "Mug", "price": 12.5, "stock": 4}


@pytest.fixture
def create(products_table, http_event, lambda_context):
    def _create(**overrides):
        event = http_event("POST", "/products", body=json.dumps({**VALID_PRODUCT, **overrides}))
        return json.loads(products.create_product(event, lambda_context)["body"])

    return _create


def _item_event(http_event, method, product_id, body=None):
    return http_event(
        method,
        f"/products/{product_id}",
        body=json.dumps(body) if body is not None else None,
        path_parameters={"productId": product_id},
    )


def test_create_product(products_table, http_event, lambda_context):
    event = http_event("POST", "/products", body=json.dumps(VALID_PRODUCT))

    response = products.create_product(event, lambda_context)
    body = json.loads(response["body"])

    assert response["statusCode"] == 201
    assert response["headers"]["Location"] == f"/products/{body['id']}"
    assert body["name"] == "Mug"
    assert body["price"] == 12.5
    assert products_table.get_item(Key={"id": body["id"]})["Item"]["stock"] == 4


def test_create_product_invalid_payload(products_table, http_event, lambda_context):
    event = http_event("POST", "/products", body=json.dumps({"name": "", "price": -1}))

    response = products.create_product(event, lambda_context)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"] == {
        "message": "Invalid product payload",
        "code": "VALIDATION",
        "details": [
            "stock is required",
            "name must not be empty",
            "price must be greater than or equal to 0",
        ],
    }
    assert products_table.scan()["Count"] == 0


def test_create_product_invalid_json(products_table, http_event, lambda_context):
    response = products.create_product(http_event("POST", "/products", body="{"), lambda_context)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"]["code"] == "INVALID_JSON"


def test_get_product(create, http_event, lambda_context):
    product = create()

    response = products.get_product(_item_event(http_event, "GET", product["id"]), lambda_context)

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == product


def test_get_product_not_found(products_table, http_event, lambda_context):
    response = products.get_product(_item_event(http_event, "GET", "missing"), lambda_context)

    assert response["statusCode"] == 404
    assert json.loads(response["body"])["error"]["code"] == "NOT_FOUND"


def test_list_products(create, http_event, lambda_context):
    ids = {create(name=f"Product {i}")["id"] for i in range(3)}

    response = products.list_products(http_event("GET", "/products"), lambda_context)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert {item["id"] for item in body["items"]} == ids
    assert body["nextCursor"] is None


def test_list_products_pagination(create, http_event, lambda_context):
    ids = {create(name=f"Product {i}")["id"] for i in range(3)}

    first = json.loads(
        products.list_products(
            http_event("GET", "/products", query={"limit": "2"}), lambda_context
        )["body"]
    )
    second = json.loads(
        products.list_products(
            http_event("GET", "/products", query={"limit": "2", "cursor": first["nextCursor"]}),
            lambda_context,
        )["body"]
    )

    assert len(first["items"]) == 2
    assert first["nextCursor"]
    assert {item["id"] for item in first["items"] + second["items"]} == ids


@pytest.mark.parametrize(
    "query", [{"limit": "0"}, {"limit": "101"}, {"limit": "abc"}, {"cursor": "not-a-cursor"}]
)
def test_list_products_invalid_query(products_table, http_event, lambda_context, query):
    response = products.list_products(http_event("GET", "/products", query=query), lambda_context)

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"]["code"] == "VALIDATION"


def test_update_product(create, http_event, lambda_context):
    product = create()

    response = products.update_product(
        _item_event(http_event, "PATCH", product["id"], {"price": 9.99, "stock": 0}),
        lambda_context,
    )
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["price"] == 9.99
    assert body["stock"] == 0
    assert body["name"] == "Mug"


def test_update_product_invalid_payload(create, http_event, lambda_context):
    product = create()

    response = products.update_product(
        _item_event(http_event, "PATCH", product["id"], {"stock": "many"}), lambda_context
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"])["error"]["details"] == ["stock must be an integer"]


def test_update_product_not_found(products_table, http_event, lambda_context):
    response = products.update_product(
        _item_event(http_event, "PATCH", "missing", {"stock": 1}), lambda_context
    )

    assert response["statusCode"] == 404


def test_delete_product(create, http_event, lambda_context):
    product = create()
    event = _item_event(http_event, "DELETE", product["id"])

    response = products.delete_product(event, lambda_context)

    assert response["statusCode"] == 204
    assert response["body"] == ""
    assert products.delete_product(event, lambda_context)["statusCode"] == 404
