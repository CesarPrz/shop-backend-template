import json

from shop import __version__
from shop.handlers import health


def test_health_returns_200(http_event, lambda_context):
    response = health.handler(http_event("GET", "/health"), lambda_context)

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"


def test_health_body(http_event, lambda_context, monkeypatch):
    monkeypatch.setenv("STAGE", "dev")

    response = health.handler(http_event("GET", "/health"), lambda_context)
    body = json.loads(response["body"])

    assert body == {
        "status": "ok",
        "service": "shop-backend",
        "version": __version__,
        "stage": "dev",
    }


def test_health_default_stage(http_event, lambda_context, monkeypatch):
    monkeypatch.delenv("STAGE", raising=False)

    body = json.loads(health.handler(http_event("GET", "/health"), lambda_context)["body"])

    assert body["stage"] == "local"
