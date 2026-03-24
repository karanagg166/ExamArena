# =============================================================
#  Exam Arena — Local Dev Checks
#  Usage:  make ci
# =============================================================

.PHONY: ci

ci:
	@echo "🐳 Building Docker images..."
	docker compose build

	@echo "🚀 Starting DB, Redis and backend..."
	docker compose up -d db redis backend

	@echo "⏳ Waiting for backend + DB to be ready (max 180s — prisma generate runs on first start)..."
	@for i in $$(seq 1 60); do \
		RESPONSE=$$(curl --silent http://localhost:8000/health 2>/dev/null); \
		if echo "$$RESPONSE" | grep -q '"healthy"'; then \
			echo "✅ Backend and DB are ready (took ~$$(($$i * 3))s)"; \
			break; \
		fi; \
		if [ $$i -eq 60 ]; then \
			echo "❌ Backend never became ready — logs:"; \
			docker compose logs backend; \
			docker compose down; \
			exit 1; \
		fi; \
		echo "Waiting... ($$i/60) — response: $$RESPONSE"; \
		sleep 3; \
	done

	@echo "📦 Prisma validate..."
	docker compose exec backend prisma validate

	@echo "📦 Prisma generate (pyclient)..."
	docker compose exec backend prisma generate --generator pyclient

	@echo "📦 Prisma DB push..."
	docker compose exec backend prisma db push --accept-data-loss

	@echo "🧹 Stopping containers..."
	docker compose down

	@echo "✅ All checks passed — safe to push!"

	docker compose exec backend pytest