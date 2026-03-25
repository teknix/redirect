# URL Cleaner & Shortener - Makefile

# Tiered environment loading
ENV_FILES := --env-file .env.docker
ifneq ("$(wildcard .env.docker.local)","")
    ENV_FILES += --env-file .env.docker.local
endif
ifneq ("$(wildcard .env.production)","")
    # In production, we ONLY use the production env file
    ENV_FILES := --env-file .env.production
endif

.PHONY: up down ps logs build restart clean

up:
	docker compose $(ENV_FILES) up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f web

build:
	docker compose $(ENV_FILES) up --build -d

restart:
	docker compose restart web

clean:
	docker compose down -v
