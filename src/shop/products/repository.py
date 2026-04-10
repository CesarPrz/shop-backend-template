"""Products persistence on DynamoDB."""

import uuid
from datetime import UTC, datetime

from botocore.exceptions import ClientError

from shop.shared.db import get_products_table


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _is_conditional_failure(exc: ClientError) -> bool:
    return exc.response["Error"]["Code"] == "ConditionalCheckFailedException"


def list_products(limit: int, start_key: dict | None = None) -> tuple[list[dict], dict | None]:
    """Return a page of products and the key to resume from, if any."""
    params = {"Limit": limit}
    if start_key:
        params["ExclusiveStartKey"] = start_key
    response = get_products_table().scan(**params)
    return response.get("Items", []), response.get("LastEvaluatedKey")


def get_product(product_id: str) -> dict | None:
    return get_products_table().get_item(Key={"id": product_id}).get("Item")


def create_product(fields: dict) -> dict:
    now = _now()
    item = {"description": "", **fields, "id": uuid.uuid4().hex, "createdAt": now, "updatedAt": now}
    get_products_table().put_item(Item=item, ConditionExpression="attribute_not_exists(id)")
    return item


def update_product(product_id: str, fields: dict) -> dict | None:
    """Update the given fields of a product. Return None when it does not exist."""
    fields = {**fields, "updatedAt": _now()}
    names = {f"#{key}": key for key in fields}
    values = {f":{key}": value for key, value in fields.items()}
    expression = "SET " + ", ".join(f"#{key} = :{key}" for key in fields)
    try:
        response = get_products_table().update_item(
            Key={"id": product_id},
            UpdateExpression=expression,
            ConditionExpression="attribute_exists(id)",
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues="ALL_NEW",
        )
    except ClientError as exc:
        if _is_conditional_failure(exc):
            return None
        raise
    return response["Attributes"]


def delete_product(product_id: str) -> bool:
    """Delete a product. Return False when it does not exist."""
    try:
        get_products_table().delete_item(
            Key={"id": product_id}, ConditionExpression="attribute_exists(id)"
        )
    except ClientError as exc:
        if _is_conditional_failure(exc):
            return False
        raise
    return True
