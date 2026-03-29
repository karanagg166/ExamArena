# Docker + Prisma + Lint Commands

Use this guide to run the full stack with Docker and manage Prisma from backend only.

## 0. Where To Run Commands

Run all commands from project root:

`/Users/karanagg/Desktop/Projects/exam-arena`

If you run commands from another folder, Docker Compose may not find `docker-compose.yml`.

## 1. Validate Setup (Before Starting)

Validate compose file syntax:

```bash
docker compose config
```

See current status of containers:

```bash
docker compose ps
```

Check logs if something fails:

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

## 2. Build Images (When To Use)

Use build when:
- Dockerfiles changed
- `requirements.txt` changed
- base dependencies changed

Build all services:

```bash
docker compose build
```

Build only backend:

```bash
docker compose build backend
```

Rebuild without cache (if build is stuck/corrupted):

```bash
docker compose build --no-cache
```

## 3. Start Services (up / up -d)

Start and keep terminal attached (best for debugging):

```bash
docker compose up
```

Start in background (`-d` = detached mode):

```bash
docker compose up -d
```

Start specific services only:

```bash
docker compose up -d db redis
docker compose up -d backend frontend
```

Build and start in one command:

```bash
docker compose up --build
docker compose up -d --build
```

## 4. Stop vs Down (When To Use)

Stop containers but keep them for quick restart:

```bash
docker compose stop
```

Start again after stop:

```bash
docker compose start
```

Stop and remove containers/networks (keeps named volumes):

```bash
docker compose down
```

Full cleanup including volumes (deletes local DB data):

```bash
docker compose down -v
```

Use `down -v` only when you intentionally want a fresh database.

## 5. Restart / Recreate Quick Commands

Restart one service:

```bash
docker compose restart backend
```

Recreate backend after compose/env changes:

```bash
docker compose up -d --force-recreate backend
```

## 6. Run Commands Inside Containers (exec)

Backend shell:

```bash
docker compose exec backend sh
```

Frontend shell:

```bash
docker compose exec frontend sh
```

Database shell:

```bash
docker compose exec db psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-exam_arena}
```

## 7. Prisma Commands (Backend Only)

Because Prisma is backend-only now, run Prisma from backend container.

Generate Python Prisma client:

```bash
docker compose exec backend prisma generate --generator pyclient
```

Push schema to database:

```bash
docker compose exec backend prisma db push
```

Force reset and push schema (destructive):

```bash
docker compose exec backend prisma db push --force-reset
```

format schema
```bash
docker compose exec backend prisma format
```

Pull current database schema into `prisma/schema.prisma`:

```bash
docker compose exec backend prisma db pull
```

Open Prisma Studio (from backend container):

```bash
docker compose exec backend prisma studio --port 5555
```

If Studio is not reachable from browser, map `5555:5555` under backend ports in `docker-compose.yml`.

## 8. Backend Lint + Type Commands (FastAPI)

### Check lint errors (Ruff):

```bash
docker compose exec backend ruff check app/
```

### Fix lint errors automatically (Ruff):

```bash
docker compose exec backend ruff check app/ --fix
```

### Check formatting errors (Black):

```bash
docker compose exec backend black --check app/
```

### Fix formatting errors automatically (Black):

```bash
docker compose exec backend black app/
```

### Check type errors (mypy):

```bash
docker compose exec backend mypy app/
```

Type errors cannot be auto-fixed — mypy tells you what is wrong and you fix them manually.

### Run all three in order (recommended before every push):

```bash
docker compose exec backend black app/
docker compose exec backend ruff check app/ --fix
docker compose exec backend mypy app/
```

## 9. Frontend Lint + Type Commands (Next.js)

### Check lint errors (ESLint):

```bash
 docker compose exec frontend npm run lint
```

### Fix lint errors automatically (ESLint):

```bash
docker compose exec frontend npm run lint -- --fix
```

### Check formatting errors (Prettier):

```bash
docker compose exec frontend npx prettier --check src/
```

### Fix formatting errors automatically (Prettier):

```bash
docker compose exec frontend npx prettier --write src/
```

### Check type errors (TypeScript):

```bash
docker compose exec frontend npx tsc --noEmit
```

Type errors cannot be auto-fixed — tsc tells you what is wrong and you fix them manually.

### Run all three in order (recommended before every push):

```bash
docker compose exec frontend npx prettier --write src/
docker compose exec frontend npx next lint --fix
docker compose exec frontend npx tsc --noEmit
```

## 10. Recommended Daily Flow

1. `docker compose up -d`
2. `docker compose ps`
3. Run your code changes
4. If Prisma schema changed:
   ```bash
   docker compose exec backend prisma db push
   docker compose exec backend prisma generate --generator pyclient
   ```
5. Before pushing code, run lint + type checks:
   ```bash
   # Backend
   docker compose exec backend black app/
   docker compose exec backend ruff check app/ --fix
   docker compose exec backend mypy app/

   # Frontend
   docker compose exec frontend npx prettier --write src/
   docker compose exec frontend npx next lint --fix
   docker compose exec frontend npx tsc --noEmit
   ```
6. Check logs if needed:
   ```bash
   docker compose logs -f backend
   ```
7. End work with `docker compose stop` (or `docker compose down` if you want cleanup)

## 11. Makefile Commands

There are two Makefiles in the project. Each command and what it does is listed below.

---

### `Makefile` — Base CI (no lint / type checks)

```bash
make ci
```
Runs the full pipeline before pushing code — builds Docker images, starts containers, waits for backend to be healthy, runs all Prisma steps (validate → generate → db push), runs pytest tests, then stops everything. Use this before every `git push`.

```bash
make test
```
Runs only backend pytest tests inside the container. Skips build, prisma, everything else. Use this while writing code to quickly check if tests pass.

```bash
make db-push
```
Runs only the three Prisma steps — validate schema, generate Python client, push schema to database. Use this after editing `schema.prisma`.

```bash
make up
```
Starts all services in the background (`docker compose up -d`). Use this to spin up your local dev environment.

```bash
make down
```
Stops and removes all running containers (`docker compose down`). Volumes are kept so your database data is safe.

---

### Quick reference — which Makefile to use

| Situation | Command |
|---|---|
| Quick check before push (no lint) | `make ci` |
| Run tests only | `make test` |
| Push Prisma schema changes | `make db-push` |
| Start dev environment | `make up` |
| Stop dev environment | `make down` |

## 12. Project Structure

View your project structure (excluding noise folders):

```bash
tree -I 'node_modules|.next|__pycache__|.git|.venv|*.pyc|postgres_data|generated' --dirsfirst
```
