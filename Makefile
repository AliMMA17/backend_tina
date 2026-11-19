.PHONY: help install dev lint format typecheck test test-cov migrate migrate-down up down logs shell clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production + dev dependencies
	pip install -e ".[dev]"
	pre-commit install

dev: ## Run development server with hot-reload
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

lint: ## Run Ruff linter
	ruff check src tests

format: ## Format code with Ruff
	ruff format src tests
	ruff check --fix src tests

typecheck: ## Run mypy type checker
	mypy src

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=src --cov-report=term-missing --cov-report=html

migrate: ## Apply Alembic migrations
	alembic upgrade head

migrate-down: ## Rollback last migration
	alembic downgrade -1

migrate-rev: ## Create a new migration (usage: make migrate-rev msg="add foo")
	alembic revision --autogenerate -m "$(msg)"

up: ## Start all services with Docker Compose
	docker compose up --build -d

down: ## Stop all services
	docker compose down

logs: ## Tail application logs
	docker compose logs -f app

shell: ## Open a shell in the app container
	docker compose exec app /bin/bash

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist build *.egg-info
