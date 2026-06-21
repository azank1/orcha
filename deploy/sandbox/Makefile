COMPOSE = docker compose -f deploy/sandbox/docker-compose.sandbox.yml --env-file .env.sandbox
ROOT    = $(shell git rev-parse --show-toplevel)

.PHONY: up down logs status seed check-env pull-models init-db

check-env:
	@test -f $(ROOT)/.env.sandbox || (echo "ERROR: .env.sandbox not found. Copy .env.sandbox.example and fill in secrets." && exit 1)

pull-models:
	@echo "Pulling nomic-embed-text model into Ollama (first pull may take a few minutes)..."
	@docker exec sandbox-ollama ollama pull nomic-embed-text || \
	  echo "WARNING: ollama pull failed — planning-discovery embeddings may not work"

up: check-env
	$(COMPOSE) up -d --build
	@echo "Waiting for Ollama to be ready..."
	@sleep 10
	@$(MAKE) -f deploy/sandbox/Makefile pull-models
	@echo ""
	@echo "Sandbox starting. Run 'make logs' to follow, 'make status' to check health."
	@echo "URL: http://localhost"

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

status:
	$(COMPOSE) ps

init-db:
	@echo "Applying PnD vector/FTS schema (idempotent)..."
	@docker exec -i sandbox-postgres psql -U postgres metaorcha \
	  < $(ROOT)/services/planning-discovery/scripts/db/001_create_vector_indices.sql
	@echo "  schema ready."

seed: init-db
	@echo "Seeding agents into registry..."
	@sleep 5
	cd $(ROOT) && REGISTRY_URL=http://localhost:8000 ./scripts/seed-sandbox-agents.sh
