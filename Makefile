.DEFAULT_GOAL := help
.PHONY: help install generate generate-check lint-api dev dev-backend dev-frontend lint lint-backend lint-frontend format typecheck typecheck-backend typecheck-frontend test test-backend test-frontend build up down migrate migrate-new ci

help: ## Показать список команд
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Установить зависимости backend, frontend и контракта
	cd backend && uv sync --dev
	cd api && pnpm install --frozen-lockfile
	cd frontend && pnpm install --frozen-lockfile

dev: ## Запустить backend и frontend
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend: ## Запустить backend на :8000
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend: ## Запустить frontend на :3000
	cd frontend && pnpm dev

lint: lint-backend lint-frontend lint-api ## Линтеры: ruff, ESLint, Prettier, tsp format

lint-backend: ## Линтер backend (ruff)
	cd backend && uv run ruff check . && uv run ruff format --check .

lint-frontend: ## Линтер frontend (ESLint, Prettier)
	cd frontend && pnpm lint && pnpm format:check

lint-api: ## Форматирование контракта (tsp format --check)
	cd api && pnpm format:check

format: ## Отформатировать код
	cd api && pnpm format
	cd backend && uv run ruff check --fix . && uv run ruff format .
	cd frontend && pnpm format

typecheck: typecheck-backend typecheck-frontend ## Проверка типов: mypy, tsc

typecheck-backend: ## mypy
	cd backend && uv run mypy .

typecheck-frontend: ## tsc
	cd frontend && pnpm type-check

test: test-backend test-frontend ## Все тесты

test-backend: ## pytest
	cd backend && uv run pytest

test-frontend: ## Vitest
	cd frontend && pnpm test

build: ## Собрать frontend
	cd frontend && pnpm build

up: ## Поднять PostgreSQL (docker compose)
	docker compose up -d

down: ## Остановить docker compose
	docker compose down

migrate: ## Применить миграции (alembic upgrade head)
	cd backend && uv run alembic upgrade head

migrate-new: ## Создать миграцию: make migrate-new m=add_event_types
	@test -n "$(m)" || { echo "Укажите название: make migrate-new m=add_event_types"; exit 1; }
	cd backend && uv run alembic revision --autogenerate -m "$(m)"

generate: ## Сгенерировать всё из контракта TypeSpec: OpenAPI и SDK frontend
	cd api && pnpm build
	@{ printf '# GENERATED из api/main.tsp командой `make generate`. НЕ ПРАВИТЬ РУКАМИ.\n'; cat api/openapi.yaml; } > api/openapi.yaml.tmp
	@mv api/openapi.yaml.tmp api/openapi.yaml
	cd frontend && pnpm generate:sdk

generate-check: generate ## Проверить, что сгенерированное закоммичено и актуально
	@test -z "$$(git status --porcelain -- api/openapi.yaml frontend/lib/api/generated)" || { git --no-pager diff --stat -- api/openapi.yaml frontend/lib/api/generated; echo "Сгенерированные файлы устарели: выполните make generate и закоммитьте результат"; exit 1; }

ci: generate-check lint typecheck test build ## Полный прогон как в CI
