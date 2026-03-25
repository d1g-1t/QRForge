.PHONY: setup up down restart migrate test lint logs clean env

ifeq ($(OS),Windows_NT)
    COPY_ENV = copy .env.example .env
    RM_CACHE = powershell -NoProfile -Command "Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; Get-ChildItem -Recurse -Filter *.pyc | Remove-Item -Force -ErrorAction SilentlyContinue"
else
    COPY_ENV = cp .env.example .env
    RM_CACHE = find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true; find . -name '*.pyc' -delete 2>/dev/null || true
endif

setup: env restart migrate
	@echo.
	@echo   QRForge is live!
	@echo   App:     http://localhost:29100
	@echo   Docs:    http://localhost:29100/docs
	@echo   Health:  http://localhost:29100/health
	@echo.

env:
	@if not exist .env $(COPY_ENV) & echo   Created .env from .env.example

restart: down up

up:
	docker compose up --build -d

down:
	-docker compose down

migrate:
	docker compose exec app alembic upgrade head

test:
	docker compose run --rm --build tests

lint:
	docker compose run --rm --build tests ruff check src/ tests/

logs:
	docker compose logs -f app worker

clean:
	docker compose down -v --rmi local
	$(RM_CACHE)
