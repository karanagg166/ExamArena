# Setup Guide

Follow this guide to run Exam Arena locally.

## Prerequisites

- Node.js 20+
- npm 10+
- PostgreSQL 15+ (or any compatible Postgres instance)

## 1. Install Dependencies

```bash
npm install
```

## 2. Configure Environment Variables

Create your local env file from the template:

```bash
cp .env.example .env
```

Then update `DATABASE_URL` in `.env` with your database connection string.

## 3. Generate Prisma Client

```bash
npx prisma generate
```

## 4. Apply Migrations

If this is your first setup or schema has changed:

```bash
npx prisma migrate dev --name init
```

## 5. Start the Development Server

```bash
npm run dev
```

Open `http://localhost:3000` in your browser.

## Quality Checks

Run these before pushing code:

```bash
npm run lint
npm run build
```

## Common Issues

### Error: DATABASE_URL is not set

- Ensure `.env` exists at project root.
- Ensure `DATABASE_URL` is present and valid.

### Prisma client import errors

- Re-run `npx prisma generate`.
- Restart the dev server after generation.
