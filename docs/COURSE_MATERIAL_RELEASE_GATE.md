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

