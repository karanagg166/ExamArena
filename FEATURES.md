# Features and Roadmap

This document tracks what is already available and what is planned for Exam Arena.

## Current Features

### Platform Foundation

- Next.js 16 App Router project initialized.
- TypeScript-enabled codebase.
- React 19 setup.

### Data Layer

- Prisma configured with PostgreSQL datasource.
- Prisma client generation configured to output under `src/generated/prisma`.
- Shared Prisma client instance implemented in `src/lib/prisma.ts`.

### Developer Experience

- ESLint configured for code quality.
- Central project docs for setup and contribution workflow.

## Planned Features

### Phase 1: Core Platform

- [ ] Authentication (email/OAuth) and role-based access.
- [ ] User profile and account settings.
- [ ] Basic dashboard for student and admin views.

### Phase 2: Exam Engine

- [ ] Question bank with categories and difficulty levels.
- [ ] Exam creation flow for admins.
- [ ] Timed exam attempts with autosave.
- [ ] Result calculation and score breakdown.

### Phase 3: Learning Experience

- [ ] Detailed review mode with explanations.
- [ ] Performance analytics by topic.
- [ ] Leaderboard and progress tracking.

### Phase 4: Operations and Scale

- [ ] Admin moderation panel.
- [ ] Audit logs for key actions.
- [ ] CI/CD automation and deployment pipelines.

## Feature Prioritization Rules

- Build core exam experience before advanced analytics.
- Favor shipping small vertical slices over large unfinished modules.
- Every shipped feature should include documentation updates.
