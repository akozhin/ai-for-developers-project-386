.DEFAULT_GOAL := help
.PHONY: help install dev dev-backend dev-frontend lint lint-backend lint-frontend format typecheck typecheck-backend typecheck-frontend test test-backend test-frontend build up down migrate migrate-new ci

help: ## Показать список команд
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Установить зависимости backend и frontend
	cd backend && uv sync --dev
	cd frontend && pnpm install --frozen-lockfile

dev: ## Запустить backend и frontend
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend: ## Запустить backend на :8000
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend: ## Запустить frontend на :3000
	cd frontend && pnpm dev

lint: lint-backend lint-frontend ## Линтеры: ruff, ESLint, Prettier

lint-backend: ## Линтер backend (ruff)
	cd backend && uv run ruff check . && uv run ruff format --check .

lint-frontend: ## Линтер frontend (ESLint, Prettier)
	cd frontend && pnpm lint && pnpm format:check

format: ## Отформатировать код
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

migrate: ## Применить миграции (появятся в sprint-02)
	@echo "Миграции появятся в sprint-02 (Alembic ещё не инициализирован)"

migrate-new: ## Создать миграцию (появятся в sprint-02)
	@echo "Миграции появятся в sprint-02 (Alembic ещё не инициализирован)"

ci: lint typecheck test build ## Полный прогон как в CI
