# Shop backend template

Serverless shop API in Python, running on AWS Lambda behind an API Gateway HTTP API and deployed with AWS SAM.

## Stack

- Python 3.12 on AWS Lambda (arm64)
- API Gateway HTTP API (payload format 2.0)
- DynamoDB (on-demand) for the product catalogue
- AWS SAM for infrastructure as code
- pytest for tests, ruff for linting and formatting
- GitHub Actions for CI

## Project layout

```
.
├── template.yaml          # SAM template (API, functions, DynamoDB table)
├── samconfig.toml         # SAM CLI defaults (dev and prod environments)
├── Makefile               # shortcuts for common tasks
├── events/                # sample API Gateway events for `sam local invoke`
├── src/                   # Lambda code (CodeUri)
│   ├── requirements.txt   # runtime dependencies bundled by `sam build`
│   └── shop/
│       ├── handlers/      # Lambda handlers (health, products)
│       ├── products/      # products repository (DynamoDB access)
│       └── shared/        # responses, validation and DynamoDB helpers
├── tests/
│   ├── conftest.py        # Lambda context, HTTP event and moto DynamoDB fixtures
│   └── unit/
├── pyproject.toml         # pytest and ruff configuration
└── requirements-dev.txt   # development tools
```

## Endpoints

| Method | Path                     | Description                          |
|--------|--------------------------|--------------------------------------|
| GET    | `/health`                | Health check                         |
| GET    | `/products`              | List products (paginated)            |
| POST   | `/products`              | Create a product                     |
| GET    | `/products/{productId}`  | Get a product                        |
| PATCH  | `/products/{productId}`  | Update some fields of a product      |
| DELETE | `/products/{productId}`  | Delete a product                     |

### Products

Products are stored in the `shop-products-<stage>` DynamoDB table (partition key `id`).

| Field         | Type    | Rules                                       |
|---------------|---------|---------------------------------------------|
| `name`        | string  | required, 1 to 120 characters               |
| `price`       | number  | required, 0 to 1,000,000, 2 decimals max    |
| `stock`       | integer | required, 0 or more                         |
| `description` | string  | optional, up to 1000 characters             |
| `category`    | string  | optional, up to 50 characters               |

`id`, `createdAt` and `updatedAt` are set by the API. `PATCH` accepts any subset of the fields above; unknown fields are rejected.

`GET /products` takes `limit` (1 to 100, default 20) and `cursor` query parameters and returns `{"items": [...], "nextCursor": "..."}`; pass `nextCursor` back as `cursor` to get the next page (`null` on the last one).

Errors use a single shape, with `details` listing each validation problem:

```json
{"error": {"message": "Invalid product payload", "code": "VALIDATION", "details": ["price is required"]}}
```

## Getting started

Requirements: Python 3.12+, and the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) plus Docker to run the API locally.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

### Tests and lint

```bash
pytest
ruff check .
ruff format .
```

### Run locally

```bash
sam build
sam local start-api
curl http://127.0.0.1:3000/health
curl -X POST http://127.0.0.1:3000/products   -H 'Content-Type: application/json'   -d '{"name": "T-shirt", "price": 19.99, "stock": 25}'

# or invoke a single function with a sample event
sam local invoke HealthFunction --event events/health.json
```

Locally, the product functions need a reachable `PRODUCTS_TABLE`: deploy the dev stack first, or point them at DynamoDB Local with `--env-vars`.

`make lint`, `make test`, `make local`, `make invoke` and `make invoke-products` wrap the commands above.

### Deploy

```bash
sam build
sam deploy                       # dev stack, defaults from samconfig.toml
sam deploy --config-env prod     # prod stack
```

The API URL is printed in the `ApiUrl` stack output.

## CI

`.github/workflows/ci.yml` runs on every push to `main` and on pull requests: ruff (lint and format check), pytest with coverage, and `sam validate --lint`.
