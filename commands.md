# Docker + Prisma Commands

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

Start specific segitrvices only:

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

Pull current database schema into `prisma/schema.prisma`:

```bash
docker compose exec backend prisma db pull
```

Open Prisma Studio (from backend container):

```bash
docker compose exec backend prisma studio --port 5555
```

If Studio is not reachable from browser, map `5555:5555` under backend ports in `docker-compose.yml`.

## 8. Recommended Daily Flow

1. `docker compose up -d`
2. `docker compose ps`
3. Run your code changes
4. If Prisma schema changed, run `docker compose exec backend prisma db push`
5. Then run `docker compose exec backend prisma generate --generator pyclient`
6. Check logs if needed: `docker compose logs -f backend`
7. End work with `docker compose stop` (or `docker compose down` if you want cleanup)
