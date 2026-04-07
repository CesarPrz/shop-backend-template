"""DynamoDB access shared between handlers."""

import os
from functools import cache

import boto3


@cache
def get_products_table():
    """Return the products table, created once per Lambda execution environment."""
    return boto3.resource("dynamodb").Table(os.environ["PRODUCTS_TABLE"])
