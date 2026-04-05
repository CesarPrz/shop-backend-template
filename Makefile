.PHONY: install lint format test build local invoke deploy

install:
	pip install -r requirements-dev.txt

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .
	ruff check --fix .

test:
	pytest --cov=shop --cov-report=term-missing

build:
	sam build

local: build
	sam local start-api

invoke: build
	sam local invoke HealthFunction --event events/health.json

deploy: build
	sam deploy
