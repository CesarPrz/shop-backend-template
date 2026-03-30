import pytest


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
