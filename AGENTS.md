# Project Rules & Development Workflow (`AGENTS.md`)

## 1. Source of Truth

* **Package Manager:** ALWAYS use `pnpm`. NEVER use `npm`, `yarn`, or `bun` unless the project is explicitly migrated.
* **Commands:** Before running project commands, inspect `commands.md`. Do not invent scripts or assume command names.
* **Dependencies / Tech Stack:** Before framework-specific or dependency-specific work, inspect the relevant `package.json` and `pnpm-lock.yaml`.
* **Environment Variables:** Inspect `.env.example` for required environment variables. Do not duplicate the full env list here.
* **Docker:** Inspect `Dockerfile`, backend Dockerfile(s), and `docker-compose.yml` before changing container behavior.
* **Database / Schema:** Inspect the project's actual schema/model files before making database changes.
* **Tests:** Inspect existing test configuration and nearby tests before writing or modifying behavior.
* Repository files are the source of truth. If assumptions conflict with repository configuration, the repository wins.

## 2. Package Manager Rules

* ALWAYS use `pnpm` for:

  * dependency installation
  * scripts
  * package additions/removals
  * builds
  * tests
  * linting
* Never create or use `package-lock.json` or `yarn.lock` accidentally.
* Before adding a dependency:

  1. inspect `package.json`
  2. inspect existing packages for equivalent functionality
  3. verify compatibility with installed framework versions
  4. add it inside the correct Docker container
* Avoid unnecessary dependencies when existing project utilities are sufficient.

## 3. Docker & Containerized Execution

* Package installation MUST run inside the appropriate running Docker container.
* Database migrations/schema operations MUST run inside the appropriate backend/application container.
* Linting, type checks, formatting, and tests SHOULD run inside Docker unless `commands.md` explicitly documents a different workflow.
* Use the correct service container for frontend/backend tasks.
* Before executing commands, inspect `commands.md` for the canonical invocation.
* Do not silently run host-level package commands when the project expects container isolation.
* Docker changes must remain portable across developer machines.
* Avoid machine-specific absolute paths, local-only mounts, or assumptions about a single developer environment.
* When modifying Docker configuration, verify:

  * build succeeds
  * containers start correctly
  * required ports are exposed
  * volume mounts are correct
  * dependencies install deterministically
  * services can communicate
  * environment variables are passed correctly

## 4. AI Model Routing

* Use the smallest capable model for routine mechanical work.
* Use stronger models for planning, architecture, difficult debugging, and non-trivial implementation.

### Default Implementation Model

* Use **Gemini 3.7** as the default coding/implementation model.

### Low-Complexity Tasks

Use **Gemini 3.7 Low** for straightforward operations such as:

* git status
* git diff inspection
* pull operations
* push operations only after explicit authorization
* branch inspection
* simple file moves
* renames
* trivial configuration edits
* command execution
* basic repository inspection

### Mechanical Validation

Prefer **Gemini 3.7 Flash Low** or another capable low-cost model for:

* lint checks
* type checks
* Ruff checks
* formatting
* test execution
* build verification
* reading obvious mechanical failures
* simple static analysis
* Equivalent lightweight GPT models may be used when appropriate.
* Complex failures must be escalated to the primary coding model.
* A low-cost model may execute validation but must not make risky architectural changes on its own.

## 5. Planning Workflow

For non-trivial work, create a plan before coding.
Examples:

* new features
* multi-file changes
* database/schema changes
* authentication/authorization
* API changes
* large refactors
* major bug fixes
* deployment architecture
* shared abstractions
* complex frontend state
* backend service redesign

### Planning Model

* Generate the first implementation plan using **Gemini 3.7 High**.
* The planning model must inspect existing code before proposing architecture.
* The plan should consider:

  * affected files
  * existing abstractions
  * installed dependencies
  * API contracts
  * schema impact
  * compatibility
  * tests
  * security
  * regression risks
  * deployment impact

### Plan Review

* If **Claude Opus 4.6** is available, use it to review the plan.
* Review for:

  * incorrect assumptions
  * missing edge cases
  * architectural problems
  * unnecessary complexity
  * SOLID violations
  * security issues
  * regression risks
  * missing tests
  * migration/deployment risks
* If Claude Opus 4.6 is unavailable, skip the review and continue.
* Do not block implementation because a review model is unavailable.

## 6. Understand Before Editing

Before modifying existing code:

1. inspect the target file
2. inspect its imports/dependencies
3. inspect callers/consumers
4. inspect nearby related files
5. inspect relevant tests
6. inspect installed package versions when relevant
7. search for existing utilities/components/services

* Never rewrite working architecture simply because another pattern is familiar.
* Prefer extending established project conventions.

## 7. Follow the Actual Tech Stack

* Never assume framework/library versions from memory.
* Inspect `package.json` and lockfiles before using version-sensitive APIs.
* If the project has a Python backend, inspect its actual dependency/config files before using framework-specific APIs.
* Do not introduce:

  * outdated Next.js patterns
  * incompatible React APIs
  * incorrect Zod versions
  * incorrect Python framework conventions
  * Jest patterns in a Vitest project
  * unsupported ORM APIs
* Match code to the repository's real versions.

## 8. SOLID & Maintainability

Follow SOLID principles where they improve maintainability.

### Single Responsibility

* Each component, service, hook, class, module, or utility should have one primary responsibility.
* Avoid mixing unrelated:

  * UI
  * API calls
  * database logic
  * validation
  * formatting
  * authentication
  * business rules
  * socket/realtime logic

### Open/Closed

* Prefer extending stable behavior rather than repeatedly rewriting it.
* New features should minimize changes to proven code paths.

### Liskov Substitution

* Implementations of shared contracts/interfaces should preserve caller expectations.

### Interface Segregation

* Avoid large interfaces/types that force consumers to depend on unrelated fields or methods.

### Dependency Inversion

* Keep business logic reasonably separated from infrastructure such as:

  * database
  * cache
  * external APIs
  * authentication
  * payments
  * message/realtime systems
* Do not over-engineer abstractions for trivial code.

## 9. Regression Safety

* New features must not unnecessarily break existing behavior.
* Before editing shared logic, inspect:

  * callers
  * tests
  * API contracts
  * types
  * database relationships
  * frontend consumers
* Prefer extending existing behavior over replacing it.
* Preserve backward compatibility unless behavior is intentionally changed.
* Bug fixes should include regression tests where practical.
* Do not delete valid tests just to obtain a green build.

## 10. Folder & File Structure

Keep code organized by responsibility.
Use existing repository conventions first.
Typical frontend/shared structure may include:

```text
src/
  app/
  api/
  components/
  features/
  hooks/
  lib/
  services/
  types/
  utils/
  schemas/
  classes/
  __tests__/
```

Backend structure should similarly separate concerns according to the framework already used.

### Components

* Reusable UI belongs in component folders.
* Feature-specific components should stay with their feature when appropriate.
* Pages should orchestrate rather than contain entire feature implementations.

### Hooks

* Reusable hooks should be placed in `hooks/` or feature-specific `hooks/`.
* Do not bury reusable hooks inside large components.

### Types

* Shared/reusable types should live in dedicated type files/folders.
* Feature-specific types may live inside the feature.
* Avoid giant type declarations embedded in unrelated UI files.

### Classes

* Reusable/domain classes should live in a dedicated `classes/`, domain, or service-oriented location consistent with the project.
* Do not scatter classes across unrelated component/API folders.

### Services

* Business/integration services should live in `services/`, `lib/`, or feature-specific service folders based on existing conventions.

### Schemas

* Validation schemas should be grouped in `schemas/` or feature-specific schema folders.
* Keep validation separate from large UI/controller files when reusable.

### API

* API code must follow the framework's required routing structure.
* Keep endpoint/controller files reasonably thin.
* Prefer:

```text
request
→ auth/permissions
→ validation
→ business/service logic
→ database/external systems
→ response
```

* Do not force extra layers onto trivial handlers.

## 11. File Size Limit

* Normal handwritten source files should generally remain below **300–350 lines**.
* If a file approaches this size, evaluate splitting by:

  * component
  * hook
  * service
  * class
  * type
  * schema
  * utility
  * domain responsibility
* Do not artificially split tightly related code just to satisfy a line count.
* Generated files, lockfiles, migrations, and machine-generated artifacts are exempt.
* Never manually refactor generated code for line-count compliance.

## 12. Reuse Before Creating

Before creating a new:

* utility
* hook
* component
* service
* class
* type
* schema
* API wrapper
* helper
  search for an existing implementation.
  Prefer reuse or extension where appropriate.
  Avoid:
* duplicate helpers
* duplicate API clients
* duplicate validation schemas
* duplicate model types
* near-identical components
* redundant service wrappers
  Do not create premature abstractions solely to remove a few duplicated lines.

## 13. New Code Requires Tests

* Meaningful new behavior should include corresponding tests.
* Tests should cover important:

  * success paths
  * failure paths
  * edge cases
  * regression scenarios
* Bug fixes should preferably:

```text
reproduce with test
→ fix implementation
→ verify regression test passes
```

* Do not add meaningless tests purely for coverage metrics.

## 14. Schema & Model Changes

Whenever database models/schema change:

* inspect affected APIs
* inspect services
* inspect validation schemas
* inspect types
* inspect frontend consumers
* inspect tests
* inspect fixtures/mocks
* inspect migrations
* update related tests
* add tests for new fields/relationships/constraints
* remove assumptions related to deleted fields
* Use the ORM/framework actually installed in the project.
* Run the documented migration/schema commands from `commands.md`.

## 15. Validation Schemas

* When backend/API types change, update and verify validation schemas.
* For TypeScript projects, inspect the actual Zod version before writing syntax.
* For Python projects, inspect the actual validation/ORM stack before assuming SQLAlchemy/Pydantic behavior.
* Keep validation aligned with:

  * nullable fields
  * optional fields
  * enums
  * database constraints
  * request shapes
  * response contracts
* Never trust client-controlled values solely because static types exist.

## 16. Mandatory Validation After Editing

After meaningful file changes, run relevant project checks inside Docker.
Check `commands.md` first for exact commands.

### Frontend / Shared

Run the configured equivalents of:

```text
pnpm lint
pnpm type-check
```

If `pnpm type-check` does not exist, do not invent it. Use the actual command documented in `commands.md` or `package.json`.

### Tests

Run the relevant test suite after code changes.
Prefer a lightweight model such as Gemini 3.7 Flash Low for execution.

### Backend / Python

If the backend uses Ruff, run the configured equivalents of:

```text
ruff check .
ruff format .
```

inside the backend container.
Do not blindly run Ruff if the repository does not actually use it.
Inspect backend tooling/configuration first.

### Schema/API Changes

Also verify relevant:

* validation schemas
* ORM models
* migrations
* API tests
* integration tests
  Target:

```text
0 newly introduced failures
```

## 17. Fix Root Causes

* Do not silence valid lint errors without understanding them.
* Do not weaken TypeScript types simply to make checks pass.
* Do not add blanket ignores unnecessarily.
* Do not weaken correct test assertions to hide implementation bugs.
* Fix the root cause.
* If a failure clearly predates the change, distinguish it from newly introduced failures and report it.

## 18. Formatting

* Use the repository's configured formatter.
* Do not introduce a second formatting tool without need.
* For Python/Ruff projects, use the project's Ruff formatting configuration.
* For JS/TS, inspect scripts/config before assuming Prettier.
* Avoid unrelated mass formatting when implementing a small feature.

## 19. Type Safety

* Maintain meaningful TypeScript types.
* Avoid `any` when practical.
* Prefer `unknown` plus narrowing for untrusted input.
* Reuse existing shared/domain types.
* Do not duplicate ORM-generated model shapes unnecessarily.
* For Python, preserve existing typing conventions and configured type-checking tools.

## 20. Error Handling

Do not silently swallow meaningful errors.
Avoid empty catches unless intentionally justified.
Error handling should:

* preserve useful internal diagnostics
* avoid leaking secrets
* return appropriate responses
* separate expected validation/domain errors from unexpected failures
* log appropriately using existing project logging patterns

## 21. Security

When relevant, check:

* authentication
* authorization
* IDOR
* validation
* injection risks
* secret exposure
* unsafe user-controlled identifiers
* unsafe database operations
* webhook verification
* payment verification
* rate limiting
* cache misuse
* CORS/security headers
  Do not trust frontend validation as a security boundary.

## 22. Environment Variables & Secrets

* Inspect `.env.example` for expected variables.
* Do not duplicate the complete variable list in this file.
* Never commit real secrets.
* Never hardcode credentials/tokens.
* Never put real secrets in tests or fixtures.
* Never expose private server secrets through public/client environment prefixes.
* Do not print sensitive values into logs.
* When adding a new required variable:

  1. update `.env.example`
  2. update relevant documentation
  3. update deployment configuration if requested/available

## 23. Docker Changes

When changing Docker configuration:

* inspect all related Dockerfiles
* inspect `docker-compose.yml`
* preserve development workflow
* avoid machine-specific assumptions
* verify service names before executing commands
* verify build context
* verify `.dockerignore`
* ensure startup commands match actual scripts
* ensure dependencies install using `pnpm`
* ensure backend tooling matches its actual ecosystem

## 24. Git Safety (NON-NEGOTIABLE)

Never automatically run:

```text
git commit
git push
```

Only commit when the user explicitly asks to **commit**.
Only push when the user explicitly asks to **push**.
Do not treat:

* implement this
* fix this
* finish this
* deploy this code
  as automatic authorization to commit/push unless the instruction clearly requests those operations.

## 25. Protect Existing Git Work

Before potentially destructive Git operations:

```text
git status
```

Inspect existing changes.
Never overwrite unrelated user work.
Avoid destructive commands such as:

```text
git reset --hard
git clean -fd
```

unless explicitly required and authorized.
Do not discard edits simply because they were not made by the current agent.

## 26. Pull / Push Tasks

* Simple pull/push/status operations may be handled by Gemini 3.7 Low.
* Before pulling, inspect local changes and avoid overwriting them.
* Push only after explicit authorization.
* Do not automatically commit changes merely because a push was requested; determine whether a commit is also explicitly requested or already exists.

## 27. Skills & Tool Usage

* Check for relevant project-specific skills only if their directories actually exist.
  Potential locations:

```text
~/.gemini/config/skills/
.agents/skills/
```

* Do not assume these directories exist.
* If present, inspect relevant skill instructions before applying them.
* Use available slash commands/automation procedures when they clearly match the task.
* Do not invoke skills blindly when normal repository tooling is more appropriate.
* If creating new project-specific skills, document them here.

## 28. Scope Control

* Keep changes focused on the requested task.
* Do not perform unrelated repository-wide refactors.
* Do not rename or restructure unrelated modules.
* Do not update dependencies unnecessarily.
* If existing architecture prevents a safe change, perform the smallest necessary refactor.

## 29. Documentation

When introducing new project-wide behavior/conventions, update relevant source-of-truth documentation such as:

```text
AGENTS.md
commands.md
README.md
.env.example
```

Do not document commands or directories that do not exist.
Keep this file concise and avoid copying information already maintained elsewhere.

## 30. Deployment Rules

Only perform post-push deployment checks after the user explicitly authorizes a push.
Inspect repository/deployment configuration to determine which services actually exist.
Do not assume every project uses Vercel, Render, and Railway simultaneously.

### Frontend / Vercel

If the frontend deploys to Vercel:

* inspect deployment status
* inspect build logs
* check runtime errors
* check SSR issues
* check hydration failures
* check missing environment variables
  Use Vercel CLI/integration when available.

### Backend

Determine the actual backend deployment provider from repository configuration.
If Render is used:

* inspect Render build/runtime status where tooling is available
  If Railway is used:
* inspect Railway deployment logs/status where tooling is available
  Do not claim a provider exists without repository evidence.

## 31. Post-Push Error Handling

After an explicitly requested push:

1. determine which deployment targets are affected
2. inspect deployment state
3. inspect build/runtime logs if available
4. identify newly introduced errors
5. fix root causes if within task scope
6. rerun local validation
7. do not create additional commits/pushes unless authorized by the user's instruction or required scope is explicit
   Do not invent health endpoints or deployment commands.

## 32. Generated Code

* Do not manually edit generated files.
* Modify the source definition/configuration and regenerate using the documented command.
  Examples may include:
* ORM-generated clients
* API-generated types
* compiled artifacts
* generated schemas
* build output
  Generated files are exempt from handwritten file-size limits.

## 33. API Design

Keep controllers/routes/endpoints reasonably focused.
Avoid one endpoint file handling all of:

* validation
* auth
* business rules
* database operations
* external services
* formatting
* notification logic
  Extract reusable logic when complexity justifies it.
  Keep simple endpoints simple.

## 34. Frontend Component Design

Avoid oversized components containing unrelated:

* UI sections
* API logic
* state machines
* business rules
* formatting
* socket logic
* modal flows
  Extract:
* components
* hooks
* schemas
* utilities
* types
* services
  when reuse/complexity warrants it.

## 35. Backend Design

Follow the existing backend framework's conventions.
Keep separation between:

* controllers/routes
* validation
* services/business logic
* persistence/models
* integration clients
* utilities
* domain classes
  Do not invent Java/Spring-like layers in a Python project or vice versa unless the existing project already follows that structure.

## 36. Database Safety

Before migrations/schema changes:

* inspect existing migration history
* inspect models
* inspect relationships
* inspect constraints
* inspect tests
  Avoid destructive migrations without explicit understanding.
  Do not drop/rename important data structures casually.
  For potentially destructive database changes, create a safe migration strategy.

## 37. Dependency Changes

Before adding/upgrading packages:

* inspect current dependency versions
* inspect lockfile
* verify necessity
* check whether an existing dependency solves the problem
* use `pnpm`
* install inside Docker
* run validation/tests afterward
  Avoid broad upgrades during unrelated feature work.

## 38. Completion Checklist

Before marking a coding task complete, verify:

* [ ] `commands.md` was checked before project commands.
* [ ] Relevant `package.json`/lockfiles were inspected when needed.
* [ ] `.env.example` was checked for env-related work.
* [ ] Existing architecture was inspected before editing.
* [ ] Existing reusable code was searched before creating duplicates.
* [ ] SOLID principles were followed where useful.
* [ ] Existing behavior was protected against regressions.
* [ ] Code was placed in the correct folder.
* [ ] Hooks/types/classes/services/components are separated appropriately.
* [ ] Handwritten files remain around or below 300–350 lines where practical.
* [ ] New meaningful behavior has tests.
* [ ] Bug fixes include regression tests where practical.
* [ ] Schema/model changes update affected tests.
* [ ] Validation schemas match API/database changes.
* [ ] Lint checks pass.
* [ ] Type checks pass where configured.
* [ ] Backend formatting/lint checks pass where configured.
* [ ] Relevant tests pass.
* [ ] Generated files were not manually edited.
* [ ] Secrets were not introduced.
* [ ] Unrelated changes were avoided.
* [ ] No commit was made without explicit instruction.
* [ ] No push was made without explicit instruction.

## 39. Standard Workflow

Use this general workflow:

```text
inspect task
→ inspect source-of-truth files
→ understand existing implementation
→ inspect dependencies when relevant
→ make plan for non-trivial work
→ review plan with Claude Opus 4.6 if available
→ implement with Gemini 3.7/default capable model
→ add/update tests
→ run lint/type/format/tests with low-cost model
→ fix root causes
→ verify regression safety
→ report completed work
```

## 40. Source-of-Truth Summary

```text
Commands            → commands.md
JS/TS dependencies  → package.json + pnpm-lock.yaml
Environment          → .env.example
Containers           → Dockerfile(s) + docker-compose.yml
Database             → actual project schema/model/migration files
Tests                → existing project test config + test directories
Skills               → only real skill directories that exist
Deployment           → repository/provider configuration
```

When documentation, assumptions, and repository files disagree, inspect the actual configuration and follow the real project state.

## 41. Core Principle

The goal is not only to make code work.
Every change should aim to:

```text
understand existing code
→ preserve current behavior
→ make the smallest maintainable change
→ follow the actual installed stack
→ keep files properly organized
→ add or update tests
→ validate inside Docker
→ fix root causes
→ avoid unnecessary Git/deployment operations
```

Use stronger models for reasoning and low-cost models for mechanical execution.
Correctness, maintainability, regression safety, security, and adherence to the actual repository always take priority over speed.
