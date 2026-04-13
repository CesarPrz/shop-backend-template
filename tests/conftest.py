import boto3
import pytest
from moto import mock_aws

from shop.shared.db import get_products_table


@pytest.fixture
def lambda_context():
    class LambdaContext:
        function_name = "test-function"
        memory_limit_in_mb = 256
        invoked_function_arn = "arn:aws:lambda:eu-west-3:123456789012:function:test-function"
        aws_request_id = "00000000-0000-0000-0000-000000000000"

    return LambdaContext()


@pytest.fixture
def http_event():
    def _make(method="GET", path="/", body=None, path_parameters=None, query=None):
        return {
            "version": "2.0",
            "routeKey": f"{method} {path}",
            "rawPath": path,
            "requestContext": {"http": {"method": method, "path": path}},
            "headers": {"content-type": "application/json"},
            "pathParameters": path_parameters,
            "queryStringParameters": query,
            "body": body,
            "isBase64Encoded": False,
        }

    return _make


@pytest.fixture
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-3")


@pytest.fixture
def products_table(aws_credentials, monkeypatch):
    monkeypatch.setenv("PRODUCTS_TABLE", "shop-products-test")
    get_products_table.cache_clear()
    with mock_aws():
        table = boto3.resource("dynamodb").create_table(
            TableName="shop-products-test",
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        )
        yield table
    get_products_table.cache_clear()
