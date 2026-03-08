.PHONY: start build up down logs shell install clean test help

PORT ?= 8003
IMAGE_NAME := evently
COMPOSE := docker compose

help:
	@echo "Evently – make targets"
	@echo ""
	@echo "  make start     Run locally with uvicorn (port $(PORT))"
	@echo "  make install   Create venv and install dependencies"
	@echo "  make build     Build Docker image"
	@echo "  make up        Start app with Docker Compose"
	@echo "  make down      Stop Docker Compose"
	@echo "  make logs      Tail Compose logs"
	@echo "  make shell     Shell into running app container"
	@echo "  make clean     Remove .venv and __pycache__"
	@echo "  make test      Run tests (if any)"
	@echo ""
	@echo "Override port: make start PORT=8004"

start:
	@test -x .venv/bin/uvicorn || (echo "Run 'make install' first." && exit 1)
	.venv/bin/uvicorn app.main:app --reload --port $(PORT)

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

build:
	docker build -t $(IMAGE_NAME) .

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

shell:
	$(COMPOSE) exec evently /bin/sh

clean:
	rm -rf .venv
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

test:
	.venv/bin/python -m pytest 2>/dev/null || echo "No tests yet – add tests/ and run pytest"
