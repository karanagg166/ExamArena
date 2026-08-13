# Project Rules & Development Workflow (`AGENTS.md`)

## 1. Package Manager & Environment
- **Package Manager:** ALWAYS use `pnpm` for installing dependencies, running scripts, and managing packages. NEVER run `npm` or `yarn`.
- **Command References:** Always inspect `@commands.md` in this repository for project-specific commands, flags, and scripts before executing tasks.

## 2. Docker & Containerized Executions (STRICT)
- **Container Isolation:** ALL package installations (`pnpm add`), database model migrations/changes, and linting commands MUST be run INSIDE the running Docker container.
- **Docker Architecture:** Ensure `Dockerfile` and `docker-compose.yml` are properly configured so the container runs reliably across this machine and all other developer systems.

## 3. Code Quality, Linting & Type Checks
After editing any file, you MUST automatically run validation checks inside the Docker container:
- **Frontend & Shared Quality:**
  - Run `pnpm lint` and `pnpm type-check` inside the container to catch TypeScript and JSX/TSX errors.
  - Check schema validations (Zod / SQLAlchemy models) whenever backend or API types change.
- **Backend Quality (Python/Ruff):**
  - Run `ruff check .` and `ruff format .` inside the backend Docker container.
  - Fix all detected formatting, typing, and lint errors immediately before marking a file edit as complete.

## 4. Git & Push Restrictions (NON-NEGOTIABLE)
- **No Unprompted Commits:** DO NOT create Git commits automatically (`git commit`).
- **No Unprompted Pushes:** DO NOT push code to remote repositories (`git push`).
- **Strict Approval:** Only run `git commit` or `git push` when I explicitly tell you to "commit" or "push".

## 5. Skills & Tool Usage
- **Custom Skills:** Proactively check and execute relevant Antigravity skills loaded in `~/.gemini/config/skills/` or `.agents/skills/`.
- **Automation Workflows:** Use available slash commands and skill procedures whenever applicable to streamline debugging, code generation, and testing.

## 6. Post-Push Deployment Error Checking
Whenever I explicitly instruct you to push the code, monitor the deployment state immediately afterward:
- **Frontend Deployments (Vercel):** Check Vercel deployment logs/status using the Vercel CLI or skill integration to detect build/hydration errors.
- **Backend Deployments (Render / Railway):** Inspect deployment build logs and status on Render or Railway to catch runtime start failures, environment variable mismatches, or database connection errors.