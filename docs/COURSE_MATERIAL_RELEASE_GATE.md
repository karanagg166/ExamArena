# Authenticated course-material production gate

Inventory before this gate: deployment smoke verifies public health and authentication
contracts but never uploads a course PDF or tests school/class evidence boundaries.
The operator synthetic-identity bootstrap is in PR #35; scoped Search Sphere client
provisioning and Vercel server configuration remain prerequisites. A passed contract
smoke cannot establish authenticated integration success.

Plan: add a separate protected-main post-deployment workflow using only dedicated
synthetic login credentials and an ownership key. Verify exact app/backend revisions,
upload newly generated public synthetic PDFs in two schools and another class, poll
actual states, retrieve a unique marker, validate the expected answer and supporting
page citations, and prove foreign-school/class evidence cannot be returned. Delete
each owned PDF and require scoped physical cleanup receipts with zero remaining
vectors and objects. Fail on missing credentials, FAILED, 503, malformed evidence
or incomplete cleanup. Course-material endpoints do not support SSE; standalone and
Quick-Clinic streaming completion have their separate gates.

Sign fixture titles and content-free journal entries. Save receipts before deletion,
recover interrupted uploads by authenticated offset-pagination and signature checks,
and preserve only signed synthetic IDs/provenance in workflow artifacts. Restore
prior same-workflow receipts before running cleanup; never save credentials,
cookies, document text, storage keys or upstream response bodies in artifacts/logs.
Test the controller offline with synthetic HTTP adapters before enabling production.
Cold-start recovery and explicit bounded-provider-failure production cases remain
separate open checks; this gate must not claim they ran.

The transport and provenance helpers are implemented first in
`app.maintenance.release_http` and `release_journal`. They use bounded responses,
cookie isolation, redirect refusal, valid generated public PDFs, HMAC-owned titles
and private atomic journals containing only signed synthetic IDs and scope labels.
Eleven offline tests cover cookie handling, refusal to follow redirects, response
bounds, PDF text visibility, receipt tampering, foreign owners, file permissions
and interrupted receipt reuse. The authenticated controller and protected workflow
remain follow-up changes; helper tests are not production acceptance.

The authenticated controller is the next increment in `course_release` and
`release_evidence`. It requires exact serving SHAs and HMAC-bound dedicated fixture
logins, uploads three fresh PDFs, polls actual states, verifies marker retrieval and
supported citations, checks school/class negatives, and requires deletion receipts
with zero vectors/derived objects and deleted originals. It rechecks retrieval after
deletion, recovers signed uploads with offset pagination and keeps the original
failure even if final cleanup also fails. Only stage labels and HTTP status codes
are printed. Fifteen offline controller cases cover success, missing/foreign
credentials, wrong revisions, FAILED, provider errors, foreign evidence/citations,
lost upload responses and invalid physical cleanup. This controller does not yet
run from production CI until the separate protected workflow/restoration change.

The protected workflow and receipt-restoration increment runs from trusted main
only, after deployment. It requires both exact revisions in main history with
successful CI and the protected `EA_RELEASE_FIXTURE_CREDENTIALS` and
`EA_RELEASE_FIXTURE_KEY` secrets. The workflow receives no database URL or Search
Sphere server key. Its controller imports only standard-library release helpers.

Before mutation, `release_receipts` downloads the previous same-workflow main
artifact through GitHub's read-only CLI token, validates owner/signatures and
restores pending cleanup. Only runs proven never to have entered the mutating step
may be skipped. Missing/expired provenance from a mutating run requires operator
reconciliation and cannot silently produce a later green run. Artifacts contain
only signed synthetic IDs, scope labels and cleanup flags; they never contain
logins, cookies, document text or Storage paths. Required missing receipts fail CI.
Six restoration cases pass in addition to the fifteen controller and eleven
transport/provenance cases. Full production acceptance remains open until scoped
server configuration is installed and the authenticated workflow actually passes.

## Cold service read recovery

Before this repair, protected run [42409361800](https://github.com/karanagg166/ExamArena/actions/runs/42409361800)
failed during exact-revision health verification with a 15-second TimeoutError,
before login or upload. A separate deployed synthetic upload probe returned 502
and identified missing server `SEARCH_SPHERE_API_KEY`; its metadata check found no
created document. Vercel management still returns 403, so that configuration step
and the full authenticated journey remain open.

Plan: give only health/readiness GET probes four bounded attempts for transient
timeouts and 502/503/504, verify the exact SHA and readiness before login, and fail
immediately on a wrong revision or malformed response. Do not retry login, uploads,
answers or cleanup assertions. Test cold recovery and exhaustion without contacting
a provider; this does not establish a forced-restart production recovery journey.

