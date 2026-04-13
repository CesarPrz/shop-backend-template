from decimal import Decimal

from shop.products import repository


def _create(**overrides):
    return repository.create_product(
        {"name": "Mug", "price": Decimal("12.50"), "stock": 4, **overrides}
    )


def test_create_product(products_table):
    item = _create()

    assert len(item["id"]) == 32
    assert item["description"] == ""
    assert item["createdAt"] == item["updatedAt"]
    assert item["createdAt"].endswith("Z")
    assert products_table.get_item(Key={"id": item["id"]})["Item"] == item


def test_get_product(products_table):
    item = _create()

    assert repository.get_product(item["id"]) == item
    assert repository.get_product("missing") is None


def test_list_products_paginates(products_table):
    ids = {_create(name=f"Product {i}")["id"] for i in range(5)}

    first, last_key = repository.list_products(limit=3)
    second, end_key = repository.list_products(limit=3, start_key=last_key)

    assert len(first) == 3
    assert {item["id"] for item in first + second} == ids
    assert end_key is None


def test_update_product(products_table):
    item = _create()

    updated = repository.update_product(item["id"], {"stock": 0, "name": "Big mug"})

    assert updated["stock"] == 0
    assert updated["name"] == "Big mug"
    assert updated["price"] == Decimal("12.50")
    assert updated["createdAt"] == item["createdAt"]


def test_update_missing_product(products_table):
    assert repository.update_product("missing", {"stock": 1}) is None
    assert "Item" not in products_table.get_item(Key={"id": "missing"})


def test_delete_product(products_table):
    item = _create()

    assert repository.delete_product(item["id"]) is True
    assert repository.get_product(item["id"]) is None
    assert repository.delete_product(item["id"]) is False
