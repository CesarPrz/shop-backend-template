"""Health check endpoint: GET /health."""

import json
import os

from shop import __version__


def handler(event, context):
    body = {
        "status": "ok",
        "service": "shop-backend",
        "version": __version__,
        "stage": os.environ.get("STAGE", "local"),
    }
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
