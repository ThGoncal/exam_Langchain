# Makefile

.PHONY: up down build rebuild logs test tests

up:
	docker compose up -d auth main streamlit

down:
	docker compose down

build:
	docker compose build

rebuild:
	docker compose down
	docker compose build
	docker compose up -d

logs:
	docker compose logs -f --tail=50

tests:
	docker compose up -d auth main
	docker compose run --rm tests
	docker compose stop auth main
