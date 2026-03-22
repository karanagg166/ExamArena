#!/usr/bin/env bash
# =============================================================
#  check.sh — Exam Arena · Develop Branch Local Check
#
#  Reads all variables from root .env (one file, no confusion).
#  Everything runs inside Docker — no local Node/Python needed.
#
#  Usage:
#    chmod +x check.sh     ← first time only
#    ./check.sh
# =============================================================

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
PASS="${GREEN}✅${NC}"; FAIL="${RED}❌${NC}"; RUN="${CYAN}▶ ${NC}"

FAILED_CHECKS=()

run_check() {
  local name="$1"; shift
  echo -e "  ${RUN} ${name}..."
  if "$@"; then
    echo -e "  ${PASS} ${name} passed"
  else
    echo -e "  ${FAIL} ${name} FAILED"
    FAILED_CHECKS+=("$name")
  fi
}

# ─────────────────────────────────────────────────────────────
#  Load root .env — this is the single source of truth
# ─────────────────────────────────────────────────────────────
ENV_FILE=".env"

if [ ! -f "${ENV_FILE}" ]; then
  echo -e "${RED}❌ No .env file found at project root.${NC}"
  echo -e "   Create one with at least DATABASE_URL set."
  echo -e "   See README for the full list of required variables."
  exit 1
fi

# Export all vars from root .env (skip comments and blank lines)
set -o allexport
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +o allexport

# Validate the one critical variable
if [ -z "${DATABASE_URL:-}" ]; then
  echo -e "${RED}❌ DATABASE_URL is not set in root .env${NC}"
  exit 1
fi

# ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}${BOLD}║   🎯  Exam Arena — Develop Branch Checks     ║${NC}"
echo -e "${BLUE}${BOLD}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Reading from: root .env${NC}"
echo -e "${YELLOW}All checks run inside Docker — no local installs needed.${NC}"
echo ""

# ─────────────────────────────────────────────────────────────
#  CHECK 1 — Docker Build
#  backend.Dockerfile runs `prisma generate --generator pyclient`
#  at build time, so a failed generate = failed build.
# ─────────────────────────────────────────────────────────────
echo -e "${BOLD}[1/4] 🐳 Docker Build${NC}"

if docker compose build \
    --build-arg DATABASE_URL="${DATABASE_URL}" \
    --build-arg NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}" \
    2>&1; then
  echo -e "  ${PASS} All Docker images built successfully"
else
  echo -e "  ${FAIL} Docker build FAILED"
  FAILED_CHECKS+=("Docker Build")
fi
echo ""

# ─────────────────────────────────────────────────────────────
#  CHECK 2 — Prisma Checks
#  You use NeonDB (cloud) so no local db container needed.
#  We start only the backend container — it reaches NeonDB directly.
# ─────────────────────────────────────────────────────────────
echo -e "${BOLD}[2/4] 📦 Prisma Checks (inside backend container → NeonDB)${NC}"

# Start backend only (no local db needed — NeonDB is remote)
docker compose up -d --no-deps backend > /dev/null 2>&1

echo -n "  Waiting for backend container"
READY=0
for i in {1..20}; do
  if docker compose exec -T backend echo "ok" > /dev/null 2>&1; then
    READY=1; break
  fi
  echo -n "."; sleep 2
done
echo ""

if [ "${READY}" -eq 0 ]; then
  echo -e "  ${FAIL} Backend container didn't start — run: docker compose logs backend"
  FAILED_CHECKS+=("Backend Container Startup")
else
  echo -e "  Backend container is up"

  run_check "Prisma Validate (schema syntax)" \
    docker compose exec -T \
      -e DATABASE_URL="${DATABASE_URL}" \
      backend prisma validate

  run_check "Prisma Generate (Python pyclient)" \
    docker compose exec -T \
      -e DATABASE_URL="${DATABASE_URL}" \
      backend prisma generate --generator pyclient

  run_check "Prisma DB Push (NeonDB connectivity)" \
    docker compose exec -T \
      -e DATABASE_URL="${DATABASE_URL}" \
      backend prisma db push --accept-data-loss
fi

echo ""

# ─────────────────────────────────────────────────────────────
#  CHECK 3 — Backend Lint (Ruff + Black)
# ─────────────────────────────────────────────────────────────
echo -e "${BOLD}[3/4] 🐍 Backend Lint (Ruff + Black)${NC}"

run_check "Ruff lint" \
  docker compose exec -T backend \
    sh -c "pip install -q ruff && ruff check app/"

run_check "Black format check" \
  docker compose exec -T backend \
    sh -c "pip install -q black && black --check app/"

echo ""
echo -e "  ${YELLOW}💡 Auto-fix Black:${NC}"
echo -e "     docker compose exec backend sh -c 'pip install -q black && black app/'"
echo ""

# ─────────────────────────────────────────────────────────────
#  CHECK 4 — Frontend (ESLint + TSC + Prettier)
# ─────────────────────────────────────────────────────────────
echo -e "${BOLD}[4/4] ⚡ Frontend Checks (ESLint · TSC · Prettier)${NC}"

docker compose up -d --no-deps frontend > /dev/null 2>&1
sleep 3

run_check "ESLint" \
  docker compose exec -T \
    -e NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}" \
    -e NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY:-}" \
    frontend npm run lint

run_check "TypeScript (tsc --noEmit)" \
  docker compose exec -T \
    -e NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}" \
    -e NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="${NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY:-}" \
    frontend npx tsc --noEmit

run_check "Prettier format check" \
  docker compose exec -T frontend \
    npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"

echo ""
echo -e "  ${YELLOW}💡 Auto-fix Prettier:${NC}"
echo -e "     docker compose exec frontend npx prettier --write 'src/**/*.{ts,tsx,js,jsx,json,css,md}'"
echo ""

# ─────────────────────────────────────────────────────────────
#  Cleanup
# ─────────────────────────────────────────────────────────────
echo -e "${YELLOW}🧹 Stopping containers...${NC}"
docker compose stop backend frontend > /dev/null 2>&1
echo ""

# ─────────────────────────────────────────────────────────────
#  Summary
# ─────────────────────────────────────────────────────────────
echo -e "${BLUE}${BOLD}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}${BOLD}║              📋  Check Summary               ║${NC}"
echo -e "${BLUE}${BOLD}╚══════════════════════════════════════════════╝${NC}"

if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
  echo ""
  echo -e "  ${GREEN}${BOLD}✅ ALL CHECKS PASSED — Safe to raise your PR! 🎉${NC}"
  echo ""
  exit 0
else
  echo ""
  echo -e "  ${RED}${BOLD}❌ The following checks FAILED:${NC}"
  for check in "${FAILED_CHECKS[@]}"; do
    echo -e "     ${RED}• ${check}${NC}"
  done
  echo ""
  echo -e "  Fix the above and re-run ${CYAN}./check.sh${NC} before raising your PR."
  echo ""
  exit 1
fi