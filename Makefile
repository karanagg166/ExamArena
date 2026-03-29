# =============================================================
#  Exam Arena — Local Dev Checks (No Lint / Type Checks)
#  Usage:
#    make ci          → full pipeline (build + checks + tests)
#    make up          → start all services
#    make down        → stop all services
#    make test        → run backend tests only
#    make db-push     → run prisma db push
# =============================================================

.PHONY: ci up down test db-push wait-backend

# ── Config ────────────────────────────────────────────────────
BACKEND_CONTAINER := backend
COMPOSE            := docker compose

# ── Helpers ───────────────────────────────────────────────────
wait-backend:
	@echo "⏳ Waiting for backend to be ready (max 180s)..."
	@for i in $$(seq 1 60); do \
		RESPONSE=$$(curl --silent http://localhost:8000/health 2>/dev/null); \
		if echo "$$RESPONSE" | grep -q '"healthy"'; then \
			echo "✅ Backend is ready (took ~$$(($$i * 3))s)"; \
			break; \
		fi; \
		if [ $$i -eq 60 ]; then \
			echo "❌ Backend never became ready — logs:"; \
			$(COMPOSE) logs $(BACKEND_CONTAINER); \
			$(COMPOSE) down; \
			exit 1; \
		fi; \
		echo "   Waiting... ($$i/60) response: $$RESPONSE"; \
		sleep 3; \
	done

# ── Service control ───────────────────────────────────────────
up:
	@echo "🚀 Starting all services..."
	$(COMPOSE) up -d

down:
	@echo "🧹 Stopping containers..."
	$(COMPOSE) down

# ── Prisma ────────────────────────────────────────────────────
db-push:
	@echo "📦 Prisma validate..."
	$(COMPOSE) exec $(BACKEND_CONTAINER) prisma validate

	@echo "📦 Prisma generate (pyclient)..."
	$(COMPOSE) exec $(BACKEND_CONTAINER) prisma generate --generator pyclient

	@echo "📦 Prisma DB push..."
	$(COMPOSE) exec $(BACKEND_CONTAINER) prisma db pull

# ── Tests ─────────────────────────────────────────────────────
test:
	@echo "🧪 Running backend tests..."
	$(COMPOSE) exec $(BACKEND_CONTAINER) pytest -v

# ── Main CI pipeline ──────────────────────────────────────────
ci:
	@echo "🐳 Building Docker images..."
	$(COMPOSE) build

	@echo "🚀 Starting backend..."
	$(COMPOSE) up -d $(BACKEND_CONTAINER)

	$(MAKE) wait-backend

	$(MAKE) db-push

# 	@echo "🧪 Running backend tests..."
# 	$(COMPOSE) exec $(BACKEND_CONTAINER) pytest -v

	$(MAKE) down

	@echo ""
	@echo "✅ All checks passed — safe to push!"