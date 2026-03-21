# Prisma Docker Commands

Since you are running everything through Docker in a monorepo (with both Python and JS generators), this cheatsheet lists the precise `docker compose exec` commands to manage your database and clients without ever needing to use your exact local Mac environment.

## 1. Pushing Schema Changes

Because `/prisma` is shared by both your containers, hitting the DB from either container works. We usually use the `backend` container to push data.

**To push changes from `schema.prisma` to the live Database:**
```bash
docker compose exec backend prisma db push
```
*(Note: You will likely see a `Generator "prisma-client" failed` warning at the end of this command. **This is completely normal!** It happens because the Python container doesn't have the JS client installed. Your database was still synced successfully.)*

**If your schema changes conflict (e.g. dropping enums) and you need to force a reset:**
```bash
docker compose exec backend prisma db push --force-reset
```

## 2. Manually Generating Clients

When you modify your `schema.prisma` file, you need to tell both your frontend and backend to update their code snippets (though a container rebuild usually does this automatically).

**To update the Python Client (FastAPI):**
```bash
docker compose exec backend prisma generate --generator pyclient
```

**To update the Javascript Client (Next.js):**
```bash
docker compose exec frontend npx prisma generate --generator client
```

## 3. Pulling Database Changes

If someone else changed the remote database and you want to pull those table structures down into your `schema.prisma`:
```bash
docker compose exec backend prisma db pull
```

## 4. Prisma Studio

While everything else can run inside docker, Prisma Studio exposes a web interface on port 5555. Unless you mapped port 5555 in your `docker-compose.yml`, it's much easier to run this specific command natively on your Mac terminal:
```bash
npx prisma studio
```
