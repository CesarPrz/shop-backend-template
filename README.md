# Shop backend template

Serverless shop API in Python, running on AWS Lambda behind an API Gateway HTTP API and deployed with AWS SAM.

## Stack

- Python 3.12 on AWS Lambda (arm64)
- API Gateway HTTP API (payload format 2.0)
- AWS SAM for infrastructure as code
- pytest for tests, ruff for linting and formatting
- GitHub Actions for CI

## Project layout

```
.
├── template.yaml          # SAM template (API + functions)
├── samconfig.toml         # SAM CLI defaults (dev and prod environments)
├── Makefile               # shortcuts for common tasks
├── events/                # sample API Gateway events for `sam local invoke`
├── src/                   # Lambda code (CodeUri)
│   ├── requirements.txt   # runtime dependencies bundled by `sam build`
│   └── shop/
│       ├── handlers/      # one module per Lambda handler
│       └── shared/        # helpers shared between handlers
├── tests/
│   ├── conftest.py        # Lambda context and HTTP event fixtures
│   └── unit/
├── pyproject.toml         # pytest and ruff configuration
└── requirements-dev.txt   # development tools
```

## Endpoints

| Method | Path      | Description  |
|--------|-----------|--------------|
| GET    | `/health` | Health check |

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

# or invoke a single function with a sample event
sam local invoke HealthFunction --event events/health.json
```

`make lint`, `make test`, `make local` and `make invoke` wrap the commands above.

### Deploy

```bash
sam build
sam deploy                       # dev stack, defaults from samconfig.toml
sam deploy --config-env prod     # prod stack
```

The API URL is printed in the `ApiUrl` stack output.

## CI

`.github/workflows/ci.yml` runs on every push to `main` and on pull requests: ruff (lint and format check), pytest with coverage, and `sam validate --lint`.
