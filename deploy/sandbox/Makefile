COMPOSE = docker compose -f deploy/sandbox/docker-compose.sandbox.yml --env-file .env.sandbox
ROOT    = $(shell git rev-parse --show-toplevel)

.PHONY: up down logs status seed check-env

check-env:
	@test -f $(ROOT)/.env.sandbox || (echo "ERROR: .env.sandbox not found. Copy .env.sandbox.example and fill in secrets." && exit 1)

up: check-env
	$(COMPOSE) up -d --build
	@echo ""
	@echo "Sandbox starting. Run 'make logs' to follow, 'make status' to check health."
	@echo "URL: http://localhost"

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

status:
	$(COMPOSE) ps

seed:
	@echo "Seeding agents into registry..."
	@sleep 5
	cd $(ROOT) && python scripts/seed-live-agents.py 2>/dev/null || \
	  uv run python scripts/seed-live-agents.py || \
	  echo "Seed script not found — register agents manually via the UI."
