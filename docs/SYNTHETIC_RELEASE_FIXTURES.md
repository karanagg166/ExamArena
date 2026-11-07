# Synthetic release identities

Pre-implementation inventory: material API tests already create isolated schools,
classes and users in local PostgreSQL. Production smoke checks public contracts,
but has no owned synthetic login/enrollment fixtures. The production Search Sphere
registry contains no ExamArena service client as of the read-only November 7 check;
Vercel configuration access currently returns 403. Full consumer acceptance remains
open.

Plan: add an operator-only, dry-run-first bootstrap for two wholly synthetic schools,
two teacher logins, two enrolled student logins and an additional class in school A.
Derive identifiers and credentials from a private release fixture key, reserve
reserved `example.com` email identities, and create all records atomically through the existing
SQLAlchemy models. Do not run the broad development seed or create exams, invitations,
notifications or external actions. Refuse partial fixtures, collisions and changed
roles, school/class grants or passwords; never overwrite existing identities.

A private, short-lived reviewed plan must bind the database target, owner and current
fixture state. Write credentials only to a new private local file after verified
application. Keep database URLs, hashes, passwords and join codes out of stdout,
CI artifacts and reports. Test dry-run immutability, atomic/idempotent creation,
concurrent delivery, stale plans, changed grants and foreign identity protection
against real PostgreSQL. No migration, dependency or model call is needed.

Subsequent release work must provision a separate scoped ExamArena client for exactly
these school tenants, approve only synthetic fixture evidence, install its server
credential in Vercel, and execute the authenticated HTTP journey from protected main
CI. Identity provisioning alone does not establish upload, retrieval, citation or
physical cleanup acceptance.

## Operator commands

Use the existing backend container with its private `DATABASE_URL` and a separately
generated `RELEASE_FIXTURE_KEY` of at least 32 characters. This key is not an app
runtime setting. Preserve it in the secret manager; rotation creates different
identities and does not recover the old fixture owner. Do not put values in command
arguments. Create a private directory outside the repository for receipts.

```sh
PYTHONPATH=backend python -m app.maintenance.release_bootstrap \
  --plan /private/release/plan.json
```

Review the target database, 13-record action and digest. The receipt binds that
target and exact owner; it contains no login values. Apply within 15 minutes:

```sh
PYTHONPATH=backend python -m app.maintenance.release_bootstrap \
  --apply /private/release/plan.json --digest REVIEWED_DIGEST \
  --credentials /private/release/credentials.json
```

The output credential file is created with mode 0600 and cannot overwrite an
existing file or follow a symlink. A failed application can leave an empty reserved
file; retain it for diagnosis and use a new path after resolving the failure.
Passwords are independently derived and bcrypt-hashed. All inserts commit together,
with no network side effects. A repeated valid fixture can be verified with a new
dry run and reused without password, role or enrollment resets. Concurrent use of
one creation plan has one winner; the other must re-read the now-existing state.
Invalid, expired or changed plans fail closed. An incomplete or altered fixture
requires operator review and is never silently repaired.

The PostgreSQL suite covers read-only dry runs, atomic creation, verified reuse,
concurrency, changed role/school/class/password, partial state, stale/foreign plans
and reserved-email collisions. File tests reject unsafe permissions, symlinks,
oversize plans and FIFOs. Only synthetic identities are used in these tests.

## Live login validation follow-up

The first production bootstrap created the expected 13 owned synthetic records.
All four real HTTP login attempts then failed at request validation with 422:
`EmailStr` rejects the `.invalid` special-use domain. No authenticated journey or
provider call occurred, and no unusable login secret was installed in CI.

Plan before correction: keep login validation strict, use reserved `example.com`
addresses, and verify every generated credential through the actual `LoginRequest`
schema. Correct only the four proven-owned fixture email fields after verifying
the full fixture state, current old addresses, derived password ownership and absence
of new-address collisions under locks. Preserve passwords and all authority grants.
Then re-run verified bootstrap and real login checks before protecting credentials
in CI. The regular bootstrap must continue refusing arbitrary changed identities.

The production ownership precheck also exposed a schema difference: the existing
Prisma-era birth-date column returns a naive timestamp, while the model/test schema
returns timezone-aware values. Normalize only that fixed synthetic UTC date during
comparison; do not change database values or weaken checks on other fields. A real
PostgreSQL regression temporarily uses the legacy column type and restores it in
`finally`, proving the same fixture can be verified and reused under both schemas.
