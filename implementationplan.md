# ExamArena Complete Testing Architecture & Implementation Task

You are working on the ExamArena repository.

The objective is to design and implement a production-quality automated testing system covering unit, component, API integration, database integration, feature/module, realtime, authorization/security, and browser end-to-end testing.

Do NOT immediately start adding tests.

First fully inspect and understand the repository.

Do not rewrite working application architecture merely to make testing easier.

Do not generate placeholder tests whose only purpose is increasing test count or coverage.

Tests must validate actual business behavior.

Do not hardcode assumptions about endpoints, schema fields, database relationships, route names, realtime implementation, UI selectors, permissions, or authentication.

Derive everything from the repository.

---

# Phase 0 — Repository Investigation

Before making changes:

Inspect:

* `AGENTS.md`
* `commands.md`
* root `package.json`
* lockfile
* Dockerfiles
* `docker-compose.yml`
* `.env.example`
* frontend testing configuration
* Playwright configuration
* Vitest configuration
* backend `requirements.txt`
* `pyproject.toml`
* `pytest.ini`
* backend test fixtures
* existing frontend tests
* existing backend tests
* existing `e2e/`
* database models/schema
* migrations
* authentication implementation
* authorization implementation
* school modules
* principal modules
* teacher modules
* student modules
* class modules
* section modules
* join-request modules
* exam modules
* question modules
* attempt modules
* result modules
* proctoring modules
* audit/activity logging
* Redis usage
* realtime/socket implementation
* background jobs
* APIs used by each major frontend feature

Build a dependency/feature map before changing tests.

Identify:

* existing tests worth keeping
* weak tests
* duplicate tests
* missing tests
* placeholder tests
* tests coupled to implementation details
* tests accessing the wrong database
* destructive tests
* flaky tests
* realtime features that are implemented versus scaffolding only

Important:

`AGENTS.md` says commands must come from `commands.md`.

If `commands.md` is missing, report that repository inconsistency and resolve the project's canonical testing commands before proceeding.

Do not invent command names silently.

---

# Phase 1 — Testing Architecture

Organize the project into clearly separated testing levels.

## Level A — Unit Tests

Test isolated business logic without PostgreSQL, Redis, network calls, or browser interaction wherever possible.

Backend targets should include actual implemented equivalents of:

* authentication utilities
* password/token validation
* role validation
* authorization helpers
* school permission checks
* membership permission checks
* teacher/class permission checks
* exam access rules
* exam availability
* scheduling decisions
* time validation
* negative marking calculation
* score calculation
* percentage calculation
* result status calculations
* question validation
* roll-number validation
* pagination utilities
* sorting/filtering logic
* audit/activity event construction
* attempt state transitions
* exam submission decisions
* automatic submission decisions
* duplicate submission protection

Frontend targets should include:

* reusable utilities
* validation schemas
* hooks
* state stores
* exam timer behavior
* form validation
* tables
* filters
* permission-aware components
* question navigation
* result rendering
* loading states
* error states
* empty states

Use the repository's existing Vitest and Testing Library stack.

Do not introduce Jest.

---

# Phase 2 — Dedicated Test Infrastructure

Create a fully isolated testing environment.

Tests must never depend on or destructively modify the normal development PostgreSQL database.

Introduce a dedicated test database such as:

`exam_arena_test`

The exact implementation must follow existing Docker and environment conventions.

The testing environment should support:

* PostgreSQL
* Redis where required
* FastAPI
* Next.js
* Playwright

Before destructive test execution, validate that the configured database is explicitly a testing database.

If the database appears to be development, staging, or production, abort the test suite.

Use database migrations/schema initialization consistently with the real application.

Never maintain a manually diverging test-only schema.

Test database lifecycle:

1. start isolated services
2. verify database safety
3. initialize database
4. apply schema/migrations
5. reset tables
6. create test fixtures
7. execute suite
8. clean generated data
9. verify cleanup

Tests should be repeatable.

Running them twice must produce the same outcome.

---

# Phase 3 — Test Data Factory Layer

Do not scatter hardcoded user creation logic across dozens of test files.

Create reusable factories/fixtures/helpers for the actual application models.

Required conceptual factories:

* principal
* teacher
* student
* school
* school membership
* join request
* class
* section
* teacher assignment
* student assignment
* exam
* question
* exam attempt
* answer
* result
* audit/activity entry

Support overrides.

For example a test should conceptually be able to request:

* principal belonging to School A
* teacher assigned to Class 10A
* student assigned to Class 10A
* password-protected future exam
* already-submitted attempt

without duplicating full setup logic.

Use deterministic values for important identity fields but randomized safe values where uniqueness matters.

---

# Phase 4 — Canonical Full Lifecycle Dataset

Create a deterministic E2E scenario.

Use dedicated testing identities.

Principal accounts:

* `principal_test@gmail.com`
* `principal_test2@gmail.com`

Use testing-only credentials controlled through the test environment.

Never commit real secrets.

Create teacher accounts approximately:

* `teacher_test1`
* `teacher_test2`
* `teacher_test3`
* `teacher_test4`
* `teacher_test5`
* `teacher_test6`
* optionally `teacher_test7`

Create enough students to exercise class isolation properly.

Prefer at least five students per important class/section.

Generate unique emails deterministically.

---

# Phase 5 — Principal 1 Registration

Register Principal 1 through the actual supported registration flow.

Test successful registration.

Also separately test:

* duplicate email
* invalid email
* empty fields
* invalid password
* password boundary conditions
* oversized inputs
* whitespace normalization where relevant
* unsupported role manipulation
* sending unexpected fields
* duplicate submission
* malformed payload

Complete Principal 1 profile/account setup.

Verify persisted database state.

Verify secrets are never exposed through API responses.

Verify role is PRINCIPAL.

Verify the user cannot arbitrarily change their role through the client/API.

---

# Phase 6 — School Creation

Principal 1 creates School Test.

Test valid creation.

Then independently test:

* missing school name
* duplicate school constraints where applicable
* invalid values
* excessively long names
* unauthorized user creating school
* teacher creating school
* student creating school
* duplicate create request
* malformed request
* ownership assignment

After successful creation verify:

* school exists in PostgreSQL
* Principal 1 belongs to it correctly
* Principal 1 has expected school permissions
* relationships are valid
* expected activity/audit log was created

Verify users outside the school cannot access private school information.

---

# Phase 7 — Principal 2 Join Request

Register `principal_test2@gmail.com`.

Complete profile setup.

Principal 2 searches/finds School Test using the actual application flow.

Principal 2 requests to join School Test.

Verify:

* membership is NOT immediately created
* request state becomes pending
* relevant Principal(s) can see the request
* requester can see their pending state
* duplicate pending request is rejected or handled idempotently
* requester cannot approve their own request
* teacher/student cannot approve a principal request
* unrelated-school principal cannot approve it
* malformed request cannot bypass authorization

Test rejection.

Verify rejected user remains outside school.

Where supported, test requesting again according to product rules.

Test approval.

Verify Principal 2 becomes an authorized principal/member only after approval.

Verify audit/activity entries for:

* request created
* request rejected where tested
* request approved

If realtime notification exists, verify the actual implemented event delivery mechanism.

Do not assume Socket.IO if it is not implemented.

---

# Phase 8 — Realtime Testing

Inspect the actual realtime implementation first.

Determine whether ExamArena currently uses:

* WebSocket
* Socket.IO
* Stream
* Redis Pub/Sub
* polling
* Server-Sent Events
* another mechanism
* or incomplete scaffolding

Write tests for the mechanism that actually exists.

Where realtime join notifications are implemented test:

* authenticated connection
* unauthenticated connection
* invalid token
* correct room/user subscription
* wrong-school subscription attempt
* join request notification
* approval notification
* rejection notification
* duplicate event
* disconnect
* reconnect
* event after reconnect
* multiple sessions
* unauthorized listener
* stale connection
* Redis temporary failure if relevant

Realtime delivery is supplemental.

Correct persistent database state remains the source of truth.

A lost realtime event must not cause permanent data inconsistency.

---

# Phase 9 — Teacher Registration & School Membership

Create 6–7 teachers.

Exercise multiple paths.

Some teachers:

* request School Test and are approved by Principal 1
* request School Test and are approved by Principal 2
* are rejected
* remain pending

Verify both legitimate principals can manage school membership according to product permissions.

Test:

* duplicate request
* request after already being member
* unauthorized approval
* teacher approving another teacher
* student approving teacher
* outsider principal approving teacher
* removing membership
* rejected user trying privileged APIs
* pending user trying privileged APIs

Verify audit/activity entries.

---

# Phase 10 — Classes and Sections

Principal 1 creates approximately four classes.

Principal 2 creates other classes where the product allows this.

Create approximately four sections for classes where practical.

Use the actual class/section model rather than forcing a fixed structure if the application differs.

Test:

* valid class
* duplicate class
* invalid class
* empty name
* wrong school
* unauthorized teacher creation
* unauthorized student creation
* outsider principal
* class deletion with relationships
* section creation
* duplicate section
* section belonging to another class
* malformed IDs
* nonexistent IDs

Critical authorization scenario:

Determine whether Principal 1 should be able to manage a class created by Principal 2 when both principals belong to the same school.

Derive expected behavior from application business rules.

Test it explicitly.

Do not invent ownership semantics.

---

# Phase 11 — Teacher-to-Class Requests / Assignments

Teachers request or are assigned to classes using the real application workflow.

Exercise:

* Principal 1 approval
* Principal 2 approval
* rejection
* pending status
* duplicate assignment
* wrong-school teacher
* wrong-school principal
* teacher self-approval attempt
* assignment to nonexistent class
* assignment to wrong section
* removed teacher
* revoked membership

Verify resulting class teacher lists.

Verify database relationships.

Verify audit/activity entries.

---

# Phase 12 — Student Registration & Membership

Create at least five students for each major class/section under test.

Exercise actual onboarding/join workflow.

Test:

* valid registration
* duplicate email
* invalid profile
* school membership
* class membership
* section membership
* pending membership
* rejection
* duplicate request
* cross-school assignment
* invalid class
* invalid section
* moving section if feature exists
* removal
* rejoining if supported

Verify the student list after every significant operation.

---

# Phase 13 — Roll Numbers

Assign roll numbers using the real application rules.

Test:

* valid roll number
* duplicate roll number in the scope where uniqueness applies
* same number in another valid scope if allowed
* missing value
* invalid characters
* negative values if numeric
* zero if invalid
* excessively large values
* updating roll number
* concurrent duplicate assignment
* unauthorized teacher
* unauthorized principal from another school
* student modifying own roll number

Verify DB uniqueness constraints and API validation agree.

---

# Phase 14 — Student Visibility / RBAC Matrix

Build an explicit role/permission matrix.

At minimum verify:

Principal:

* can access expected students across their school

Teacher:

* can access only students allowed by their assignment/permissions

Student:

* can access only permitted personal/class-level information

Outside-school users:

* cannot access School Test private information

Test visibility through both:

* backend APIs
* frontend UI

Never trust UI hiding as authorization.

Call protected APIs directly with unauthorized identities.

Test IDOR scenarios by replacing IDs in requests.

Examples:

* Student A requesting Student B's private result
* Teacher from Class A requesting Class B data
* principal from School B requesting School A data
* modifying IDs in URLs
* modifying request bodies
* forged role fields

Every authorization test must verify backend rejection.

---

# Phase 15 — Exam Creation

Create exams using Principal and Teacher roles according to actual permissions.

Cover multiple exam configurations.

Exam types should include combinations of:

* public/access-controlled
* password protected
* no password
* negative marking
* no negative marking
* answer key release enabled/disabled where supported
* result instant/delayed where supported
* different durations
* different question counts
* scheduled
* unscheduled/immediate if supported

Time scenarios:

* past
* currently active
* future
* exact boundary before start
* exact boundary at start
* exact boundary at end
* just after end

Use deterministic/frozen time where appropriate.

Do not make tests wait in real time for long exam durations.

Test invalid configurations:

* zero duration
* negative duration
* end before start
* impossible schedule
* empty exam
* invalid marks
* negative marks inconsistent with rules
* malformed password
* missing required values
* wrong class
* wrong school
* unauthorized creator
* duplicate exam submission

Verify audit/activity entries.

---

# Phase 16 — Questions

Create representative questions supported by the application.

Test all implemented question types.

Examples only if supported:

* MCQ
* multiple-select
* true/false
* descriptive

Test:

* valid question
* no correct answer
* multiple correct answers when invalid
* invalid option index
* duplicate options
* zero marks
* negative marks
* invalid question type
* empty text
* oversized text
* updating question after students started exam
* deleting question after attempt creation
* unauthorized modification

Respect actual product rules when deciding expected behavior.

---

# Phase 17 — Exam Discovery

Using different students verify exam visibility.

Test:

* correct class
* wrong class
* correct section
* wrong section
* public exam
* restricted exam
* future exam
* active exam
* expired exam
* password exam
* unpublished/draft exam where applicable

A student must not gain access merely by knowing an exam ID.

Call exam APIs directly.

---

# Phase 18 — Password-Protected Exams

Verify:

* correct password
* wrong password
* empty password
* leading/trailing whitespace behavior
* case sensitivity according to product rule
* direct start endpoint without password validation
* repeated invalid attempts
* password never returned through API
* password never leaked into logs
* password never exposed to unauthorized frontend data

If rate limiting exists, test it.

If it does not exist, identify this as a security recommendation rather than inventing functionality.

---

# Phase 19 — Attempt Lifecycle

Create multiple student attempts.

Test:

* valid start
* duplicate start
* starting before exam
* starting after exam
* wrong class
* wrong student
* unauthorized attempt ID access
* save answer
* update answer
* unanswered question
* navigation
* reconnect/reload
* attempt state persistence
* submit
* duplicate submit
* editing after submit
* calling answer endpoint after submit
* expired attempt
* server-authoritative time enforcement

Do not rely on the frontend timer as the security boundary.

Verify backend rejects submissions/answer modifications based on authoritative attempt/exam timing.

---

# Phase 20 — Timer & Automatic Submission

Test timer logic separately from browser E2E.

Verify:

* backend stores authoritative start/end information
* browser reload cannot reset exam time
* new tab cannot reset exam time
* altered frontend timer cannot extend server deadline
* client clock changes cannot extend attempt
* submission exactly at deadline
* submission immediately after deadline
* network interruption near deadline

If automatic server-side submission exists, test it.

If automatic submission is primarily frontend-driven, verify the backend still prevents work after the deadline.

Do not use long real-time waits.

Use controlled/frozen time or appropriately structured test configuration.

---

# Phase 21 — Answer Submission & Scoring

Create students with intentionally different answer patterns:

* all correct
* all wrong
* partially correct
* unanswered questions
* mixed correct/wrong/unanswered

Verify exact scoring.

For negative marking verify:

* correct mark
* wrong-answer deduction
* unanswered behavior
* lower bound behavior if score cannot go below zero
* decimal precision
* rounding rule
* percentage calculation

Expected values must be independently computed by the test rather than copied from the implementation under test.

---

# Phase 22 — Result Publication

Exercise both supported result behaviors.

Where configured for instant result:

After submission verify the student sees allowed information immediately.

Where configured for delayed publication:

Verify result remains hidden until teacher/principal publishes it.

After publishing verify visibility changes.

Test:

* student accessing unpublished result through API
* answer-key visibility before allowed
* publishing twice
* unpublishing if supported
* teacher publishing unrelated exam
* wrong-school principal publishing result
* student attempting publication
* direct URL manipulation

---

# Phase 23 — Answer Key Security

Verify the answer key is unavailable before the configured release condition.

Test frontend and direct API access.

Inspect API responses used while taking the exam.

Correct answers must not accidentally be included in question payloads unless intentionally required by product design.

Check:

* initial exam response
* question response
* network/API representation
* browser state data
* serialized server responses

Treat accidental answer-key exposure as a critical test failure.

---

# Phase 24 — Student Result Access

Students should see only results they are authorized to see.

Test:

* own result
* own result for another exam
* unpublished result
* result from another class
* another student's result
* forged result ID
* forged attempt ID
* invalid filters

Clarify the product rule around classmates.

Do not automatically expose detailed individual results merely because two students share a class unless the application explicitly intends that behavior.

Default to privacy-first expectations for individual student marks.

---

# Phase 25 — Teacher Result Access

Teachers should access results according to their assigned classes/exams.

Test:

* own class
* assigned exam
* unrelated class
* unrelated school
* removed assignment
* inactive teacher

Exercise:

* exam-wise filtering
* student-wise filtering
* class filter
* section filter
* score/result filter
* date filter where supported
* sorting ascending/descending
* pagination
* empty results
* invalid filters
* combined filters

Verify totals and pagination metadata.

---

# Phase 26 — Principal Result Access

Principal users should access school-wide result information according to product permissions.

Test:

* all school students
* class
* section
* teacher
* exam
* student
* score range
* result status
* sorting
* pagination
* combined filters

Principal from another school must never access these results.

---

# Phase 27 — Audit & Activity Logs

Investigate whether activity/audit logging already exists.

Do not invent tables before understanding the current schema.

If the application intends audit logs, test logs for important operations such as:

* principal registration/setup
* school creation
* school join request
* join approval
* join rejection
* teacher approval
* teacher rejection
* class creation
* section creation
* teacher assignment
* student assignment
* roll-number change
* exam creation
* exam update
* exam publication
* exam deletion
* result publication
* permission-sensitive destructive operations

Each entry should capture the fields supported by the actual design, potentially including:

* actor
* action
* target type
* target ID
* timestamp
* school
* metadata

Do not log passwords, authentication tokens, exam passwords, or other secrets.

Authorization:

* Principal: visible according to school policy
* Teacher: denied unless explicitly supported
* Student: denied
* outsider: denied

Verify direct audit-log API access, not only hidden navigation.

---

# Phase 28 — Concurrency / Race Conditions

Add integration tests for important races.

Examples:

Two principals approve the same request simultaneously.

Expected:

* one consistent membership
* no duplicates
* deterministic final request state

Also test where applicable:

* same teacher approved twice
* same student assignment concurrently
* duplicate roll number concurrently
* student submits exam twice simultaneously
* answer update racing with final submission
* two result publications
* exam modification while attempt starts

Database constraints should provide final protection where appropriate.

---

# Phase 29 — Database Integrity Tests

Verify critical foreign keys and unique constraints.

Examples where applicable:

* memberships reference valid users/schools
* sections reference valid classes
* students reference valid memberships
* attempts reference valid exams/users
* answers reference valid attempts/questions
* results reference correct attempts
* duplicate memberships prevented
* duplicate assignments prevented
* roll-number uniqueness enforced at appropriate scope

Test deletion behavior.

Determine whether relationships use:

* cascade
* restrict
* soft deletion
* archival

Test according to actual schema.

---

# Phase 30 — Redis Tests

Identify every Redis feature.

Potential examples:

* caching
* rate limiting
* sessions
* queues
* Pub/Sub
* exam state
* realtime events

For every real use:

Test normal behavior.

Then test reasonable failure behavior:

* missing cache
* stale cache
* Redis unavailable
* duplicate message
* expired key
* reconnect

Persistent business truth must not depend solely on volatile cache unless intentionally designed that way.

---

# Phase 31 — Frontend Component Tests

Use Vitest + React Testing Library + user-event.

Use MSW for mocked API boundaries.

Prioritize:

* registration
* login
* school setup
* join request
* approval dialogs
* classes
* sections
* students table
* teachers table
* exams
* question editor
* exam-taking interface
* timer
* submission dialog
* results
* filters
* audit log UI
* permission-aware navigation

Test user-observable behavior rather than implementation details.

Avoid snapshots for large dynamic pages unless there is a strong reason.

---

# Phase 32 — Browser E2E Architecture

Use Playwright.

Do not place every edge case in E2E.

Create several focused workflows rather than one enormous test.

Recommended conceptual E2E suites:

* authentication lifecycle
* school/principal lifecycle
* teacher membership lifecycle
* classes/sections lifecycle
* student lifecycle
* exam authoring lifecycle
* student exam lifecycle
* results lifecycle
* authorization isolation
* audit-log lifecycle

Then add one golden-path full-system scenario connecting them.

Use reusable Playwright fixtures/page abstractions only where they reduce duplication.

Do not build an overly complex Page Object hierarchy.

---

# Phase 33 — Golden Full-System Scenario

Create one comprehensive deterministic workflow:

Principal 1 registers.

Principal 1 completes setup.

Principal 1 creates School Test.

Principal 2 registers.

Principal 2 completes setup.

Principal 2 requests School Test.

Verify Principal 2 is not yet a member.

Principal 1 approves request.

Verify Principal 2 membership.

Create several teachers.

Teachers request school membership.

Use both principals for approvals and rejection cases.

Create classes and sections.

Use both principals.

Assign/request teachers to classes.

Exercise cross-principal permissions.

Create multiple students per important class.

Approve students.

Assign students to class/section.

Assign roll numbers.

Verify visibility matrix.

Create several exams:

* immediate/active
* future
* expired
* password protected
* unprotected
* negative marking
* no negative marking
* instant result where supported
* delayed result where supported

Students discover eligible exams.

Verify unauthorized exams remain hidden and inaccessible directly.

Students attempt exams.

Use multiple scoring patterns.

Submit exams.

Verify automatic timing restrictions.

Verify instant-result behavior.

Publish delayed results through teachers/principals.

Verify result permissions.

Exercise result filters and sorting.

Verify audit/activity entries throughout.

Finally perform controlled cleanup.

---

# Phase 34 — Cleanup Strategy

Do not rely only on deleting records one-by-one from browser tests.

Use isolated test DB lifecycle as the primary cleanup strategy.

Each integration test should isolate its own state.

The golden E2E suite may share scoped setup inside its own worker/run.

After completion verify no leaked data remains.

Do not delete development data.

Do not delete production data.

Do not use wildcard destructive commands without test-database safety guards.

---

# Phase 35 — Security Tests

Add high-value authorization and input-security tests.

Prioritize:

* IDOR
* horizontal privilege escalation
* vertical privilege escalation
* role manipulation
* cross-school access
* cross-class access
* accessing another attempt
* accessing another result
* modifying submitted attempts
* answer-key leakage
* exam password leakage
* mass-assignment attempts
* unauthorized audit-log access
* malformed identifiers
* oversized payloads
* unexpected fields

Do not perform destructive penetration testing against external systems.

Keep security tests scoped to the local test environment.

---

# Phase 36 — Accessibility & Browser Coverage

For critical E2E paths verify major accessibility problems where practical.

Consider Playwright accessibility tooling such as axe if it fits the project.

Run primary E2E tests on Chromium.

Run an appropriately sized critical subset on Firefox and WebKit if stable and affordable.

Do not multiply every expensive test across browsers unnecessarily.

---

# Phase 37 — Test Coverage

Generate frontend and backend coverage.

Do not optimize solely for coverage percentage.

Critical business logic should have stronger coverage than cosmetic UI.

Suggested direction:

* business/domain logic: very high
* authorization logic: very high
* scoring/timing/result logic: very high
* API integration: strong coverage of critical endpoints
* UI components: critical states/interactions
* E2E: major business journeys rather than every line

Identify meaningful uncovered business paths in the final report.

---

# Phase 38 — Test Naming

Tests should describe behavior.

Prefer names conceptually like:

`student cannot access result belonging to another student`

rather than:

`test_result_4`

Use consistent grouping by business feature.

---

# Phase 39 — Flakiness Rules

Do not use arbitrary sleeps.

Wait for explicit:

* API responses
* UI states
* database conditions
* realtime events

Do not depend on test ordering unless a suite explicitly uses isolated shared lifecycle state.

Independent tests must remain order-independent.

Time-dependent tests must use deterministic time where practical.

---

# Phase 40 — CI Strategy

Create or update CI only after inspecting the repository's current GitHub Actions setup.

Recommended conceptual stages:

Fast:

* static checks
* frontend unit/component tests
* backend unit tests

Integration:

* PostgreSQL
* Redis
* backend integration tests

E2E:

* build/start full stack
* initialize test DB
* Playwright critical workflows
* upload Playwright traces/screenshots/reports on failure

Coverage:

* frontend report
* backend report

Avoid running the most expensive E2E suite on every trivial operation if existing repository CI conventions provide a better strategy.

---

# Phase 41 — Failure Artifacts

For E2E failures preserve useful debugging information:

* screenshot
* Playwright trace
* relevant console output
* network failure information
* server logs where appropriate

Never include secrets.

---

# Phase 42 — Dependencies

First inspect existing dependencies.

Do not reinstall packages that already exist.

Frontend already has the primary required testing stack.

Only add packages when there is a clear gap.

Potential additions to evaluate:

Backend:

* Faker
* factory-boy
* freezegun
* Hypothesis
* pytest-xdist
* Testcontainers if appropriate

Frontend/E2E:

* axe accessibility tooling if appropriate

Check compatibility with actual installed versions.

All JavaScript dependency installation must follow AGENTS.md and use pnpm inside the correct container.

Backend dependency changes must follow the repository's Python/container workflow.

---

# Phase 43 — Files/Structure

Do not blindly create this exact tree.

First map existing test structure and extend its conventions.

However the finished project should conceptually distinguish:

frontend unit/component tests

backend unit tests

backend API integration tests

backend DB integration tests

feature tests

realtime tests

E2E tests

fixtures/factories

test-data builders

test utilities

Playwright setup

coverage config

CI configuration

Avoid a giant single test file.

Avoid duplicating factories in multiple modules.

---

# Phase 44 — Implementation Order

Implement in this order:

1. repository/test audit
2. fix testing-environment safety
3. dedicated PostgreSQL test DB
4. Redis testing strategy
5. reusable factories/fixtures
6. core unit tests
7. authorization tests
8. database/API integration tests
9. school/principal feature tests
10. teacher tests
11. student tests
12. classes/sections tests
13. exam/question tests
14. attempts/timing/scoring tests
15. result tests
16. audit/activity log tests
17. realtime tests if implementation exists
18. frontend component tests
19. focused Playwright flows
20. golden full-system Playwright flow
21. cross-browser critical smoke tests
22. coverage
23. CI integration
24. final documentation

After each phase run the relevant existing validation commands rather than waiting until everything is implemented.

---

# Phase 45 — Final Verification

Before considering the task complete verify:

* frontend unit tests pass
* backend unit tests pass
* backend integration tests pass
* PostgreSQL isolation works
* Redis-related tests pass
* permission matrix passes
* Playwright tests pass
* golden lifecycle passes
* repeated suite execution passes
* cleanup succeeds
* lint passes
* type checks pass
* backend static checks pass
* build passes
* CI configuration is valid

Run according to repository command rules.

---

# Required Final Report

At completion provide:

## Existing state

Explain what testing existed before the work.

## New testing architecture

Explain each testing layer.

## Dependencies

List what was already installed and what was added.

Explain why each new dependency was necessary.

## Test database

Explain isolation and cleanup.

## Coverage

Report frontend/backend coverage.

## Feature matrix

For every major ExamArena feature report:

* tested
* partially tested
* not implemented
* intentionally excluded

## Authorization matrix

Summarize Principal/Teacher/Student permissions verified.

## Realtime

Explain actual realtime implementation discovered and what was tested.

## E2E scenarios

Summarize browser workflows.

## Edge cases

Summarize important failure cases tested.

## Audit logs

State operations tested and access-control behavior.

## Remaining risks

List gaps that require application changes rather than tests.

---

# Important Constraints

Do not change business behavior simply so a test passes.

If a test exposes a real application bug, report the bug and fix it only after understanding expected behavior.

Do not weaken assertions.

Do not skip tests just to make CI green.

Do not use development database records as fixtures.

Do not rely on existing manually created accounts.

Do not depend on external production services where a deterministic local/test equivalent exists.

Do not expose secrets.

Do not introduce Jest.

Do not replace Vitest.

Do not replace Playwright.

Do not replace pytest.

Do not introduce unnecessary frameworks.

Do not assume Socket.IO.

Inspect the implementation.

Do not create hundreds of shallow tests.

Prefer meaningful business assertions.

The final goal is not merely high test coverage.

The goal is proving that ExamArena's real user lifecycle, authorization boundaries, examination rules, data integrity, timing, scoring, results, school isolation, realtime behavior, and auditability remain correct under both normal and adversarial edge cases.
