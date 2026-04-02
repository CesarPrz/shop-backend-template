"""Health check endpoint: GET /health."""

import os

from shop import __version__
from shop.shared.responses import json_response


def handler(event, context):
    return json_response(
        200,
        {
            "status": "ok",
            "service": "shop-backend",
            "version": __version__,
            "stage": os.environ.get("STAGE", "local"),
        },
    )
