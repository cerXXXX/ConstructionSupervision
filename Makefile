# Все команды проекта. Подробности — docs/runbook.md
.DEFAULT_GOAL := help
SHELL := /bin/bash

COMPOSE     := docker compose
COMPOSE_DEV := docker compose -f docker-compose.yml -f docker-compose.dev.yml

# Сопоставление короткого имени сервиса (s=plan) с именем контейнера и портом.
SERVICES := plan site analysis vision gateway
PORT_plan := 8001
PORT_site := 8002
PORT_analysis := 8003
PORT_vision := 8004
NAME_plan := plan-service
NAME_site := site-service
NAME_analysis := analysis-service
NAME_vision := vision-service
NAME_gateway := gateway

.PHONY: help up down dev restart logs ps health seed demo reset test lint fmt contracts migrate models backup e2e pull

help: ## Показать список команд
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

pull: .env ## Забрать опубликованные образы из ghcr (нужен docker login ghcr.io)
	$(COMPOSE) pull

up: .env ## Поднять весь стек
	$(COMPOSE) up -d --build

dev: .env ## Поднять стек в режиме разработки (hot-reload)
	$(COMPOSE_DEV) up --build

down: ## Остановить стек
	$(COMPOSE) down

restart: ## Перезапустить сервис: make restart s=plan
	$(COMPOSE) restart $(NAME_$(s))

logs: ## Логи сервиса: make logs s=plan [f=1]
	$(COMPOSE) logs $(if $(f),-f,) --tail=200 $(NAME_$(s))

ps: ## Состояние контейнеров
	$(COMPOSE) ps

health: ## Опросить /health/ready всех поднятых сервисов
	@for s in $(SERVICES); do \
		port=$$(make -s _port s=$$s); \
		[ -z "$$port" ] && continue; \
		printf '%-18s ' "$$s"; \
		curl -fsS -m 3 "http://localhost:$$port/health/ready" 2>/dev/null || echo "недоступен"; \
		echo; \
	done

_port:
	@echo $(PORT_$(s))

seed: ## Загрузить демо-данные
	./scripts/seed.sh

demo: ## Демо-сценарий: три «дня» объекта с заложенными отклонениями
	./scripts/demo.sh

reset: ## Полная очистка данных: тома БД, бакеты, очередь
	$(COMPOSE) down -v

test: ## Тесты: make test [s=plan]
	@if [ -n "$(s)" ]; then \
		cd services/$(NAME_$(s)) && PYTHONPATH=. pytest -q; \
	else \
		for d in services/*/tests; do \
			svc=$$(dirname $$d); echo "── $$svc"; \
			(cd $$svc && PYTHONPATH=. pytest -q) || exit 1; \
		done; \
	fi

lint: ## Линт всех Python-сервисов
	ruff check --config tools/ruff.toml packages services scripts
	ruff format --check --config tools/ruff.toml packages services scripts

fmt: ## Автоформатирование
	ruff format --config tools/ruff.toml packages services scripts
	ruff check --fix --config tools/ruff.toml packages services scripts

contracts: ## Пересобрать снапшоты OpenAPI и TS-клиент
	./scripts/contracts.sh

migrate: ## Создать миграцию: make migrate s=plan m="описание"
	cd services/$(NAME_$(s)) && PYTHONPATH=. alembic revision --autogenerate -m "$(m)"

models: ## Скачать веса моделей в data/models
	./scripts/fetch_models.sh

e2e: ## Сквозной сценарий на поднятом стеке
	./scripts/e2e.sh

backup: ## Дамп баз и зеркало бакетов
	./scripts/backup.sh

.env:
	@echo "Нет .env — создаю из шаблона. Проверьте пароли и ключи перед продом."
	cp .env.example .env
