.PHONY: help build up down test test-models test-contact logs shell init-test-db migrate-create migrate-upgrade migrate-downgrade

help:
	@echo "Available commands:"
	@echo "  make build            - Build Docker containers"
	@echo "  make up               - Start all services"
	@echo "  make down             - Stop all services"
	@echo "  make init-test-db     - Initialize test database"
	@echo "  make test             - Run all tests"
	@echo "  make test-models      - Run model tests only"
	@echo "  make test-contact     - Run contact model tests only"
	@echo "  make migrate-create   - Create a new migration (use MSG='description')"
	@echo "  make migrate-upgrade  - Apply migrations"
	@echo "  make migrate-downgrade- Rollback last migration"
	@echo "  make logs             - Show logs"
	@echo "  make shell            - Open backend shell"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

init-test-db:
	docker-compose exec db psql -U crm_user -d crm_db -c "CREATE DATABASE crm_test;" || true

test:
	docker-compose run --rm backend uv run pytest

test-models:
	docker-compose run --rm backend uv run pytest tests/models/

test-contact:
	docker-compose run --rm backend uv run pytest tests/models/test_contact.py -v

test-coverage:
	docker-compose run --rm backend uv run pytest --cov=app --cov-report=html --cov-report=term

migrate-create:
	docker-compose run --rm backend uv run alembic revision --autogenerate -m "$(MSG)"

migrate-upgrade:
	docker-compose run --rm backend uv run alembic upgrade head

migrate-downgrade:
	docker-compose run --rm backend uv run alembic downgrade -1

logs:
	docker-compose logs -f

shell:
	docker-compose run --rm backend bash

backend-shell:
	docker-compose exec backend bash