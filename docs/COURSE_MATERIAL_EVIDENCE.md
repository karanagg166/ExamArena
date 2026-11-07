# Reauthorizing Search Sphere evidence

Course material search and answers re-fetch each upstream document identity from
ExamArena's PostgreSQL catalog after the upstream call. The row must still be READY
in the selected school, academic subject, class collection and optional document
type. Both external material IDs and previously recorded Search Sphere internal IDs
remain supported. Fresh query results replace SQLAlchemy's identity-map values so
an earlier loaded material cannot mask a status or scope change.

Unknown or unauthorized search results reject the entire response with a safe 502.
An invalid citation also rejects the entire answer. Dropping the citation while
returning its answer text could disclose the evidence. Metadata such as material ID,
filename, title and document type comes from the authorized local row, rather than
unverified upstream metadata. Citation references must match the supplied source
numbers. Version and chunk IDs are preserved when supplied by the versioned API.
An answer without citations uses the client's deterministic no-evidence response.

This complements Search Sphere's own scope and version checks. Doctor/patient rules
belong to Quick-Clinic; school enrollment and class access belong to ExamArena.
The broader release ledger still tracks seeded production journeys and remaining
permission checks. Unit tests use synthetic upstream adapters; HTTP tests exercise
the actual routes and local PostgreSQL catalog, including cross-school evidence.

## Catalog class scope follow-up

Inventory before repair: `permissions.resolve_user_search_school_id` already checks
school affiliation and rejects an explicitly requested different student class.
`evidence_access.py` reauthorizes RAG evidence against its selected collection.
However, the catalog list route without a class filter only restricts school, and
the individual GET route only compares school IDs. A student can consequently read
another class's catalog metadata in the same school. Upload also lacks a check that
its supplied class belongs to the teacher's school.

Plan: retain the existing staff school-wide policy, resolve the student's current
enrolled class from PostgreSQL, and apply it to both catalog rows and pagination
counts. School-wide materials remain visible alongside the enrolled class. Reject
other-class individual reads and cross-school class uploads before calling Search
Sphere. Reuse the existing permissions/CRUD/router layers and existing SchoolClass
and Student tables; no migration or new dependency is needed. Add real PostgreSQL
HTTP regressions for permitted and denied catalog reads, bounded pagination and
rejected uploads with zero upstream calls before changing behavior.

The repair applies the school and enrolled-class predicates in SQL to both rows
and counts, before pagination. Students can read school-wide and their own class's
metadata; another class's individual material returns 404. Missing enrollment fails
closed rather than becoming an unrestricted staff scope. Staff keep the existing
school-wide policy. Supplied classes must belong to the authorized school, including
on upload before storage or provider work. Synthetic PostgreSQL HTTP regressions
reproduced the original list/read/upload failures and now pass with the existing
course-material API suite (26 cases). Black/Ruff and permission/CRUD type checks
pass. The broader domain mypy check has the same 17 existing diagnostics as main
(Pydantic aliases and route parameter defaults); no new diagnostics were introduced.

## Physical cleanup receipt

Before this follow-up, deletion removes the local CourseMaterial after Search Sphere
revokes it, but ExamArena cannot verify the eventual vector/private-object cleanup
through its authenticated API. Add a staff-only read using the freshly resolved
school tenant and stable external material ID. The upstream receipt survives local
deletion and independently enforces that tenant. Preserve the existing staff
school-wide policy; students cannot use this management endpoint. Accept only a
validated receipt, never treat 503 or 404 as successful physical cleanup, and do not
return raw upstream details. Reuse the existing client/permissions and Pydantic
schemas; no migration, inference or dependency is required. Verify foreign-school
denial, staff/student roles, pending/complete states and malformed receipts.

`GET /api/v1/course-materials/{material_id}/cleanup` implements that contract. It
resolves staff affiliation from the session, delegates `school_<id>` and the stable
external material ID, and returns only strict validated receipt fields. A completed
receipt requires zero vector/derived-object counts and a deleted original. Foreign
scope/missing receipts return 404; malformed, inconsistent or unavailable receipts
return unverified 503. Browser tenant headers are ignored and success responses are
private/no-store. Fifty-seven PostgreSQL API/client cases passed across cleanup,
catalog authorization and existing material behavior; Ruff, Black and targeted
schema/client type checks passed. Production physical cleanup proof remains pending.

## Caller revocation during upstream work

Before this follow-up, search/answer re-fetch source catalog rows after inference,
but retain the caller's school/class authorization from before the upstream call.
A teacher can move schools or a student can change enrollment during that interval.
SQLAlchemy's identity map can also retain the earlier affiliation object. Plan:
re-read only current role and affiliation/enrollment columns after upstream work,
reject changed school/class access before returning evidence, and use those fresh
column reads for cleanup receipts as well. Keep the established initial role and
school-wide/class policies. Reproduce both endpoints with another PostgreSQL
session changing caller grants during the synthetic provider call, then prove the
answer/search evidence is withheld. No model, schema or dependency change.

The response boundary now reads current user role and school/enrollment columns
directly from PostgreSQL after upstream search, answer and cleanup work. These
column projections bypass cached ORM affiliation objects. A changed role, missing
profile, changed school or disallowed current class withholds the response with
403; school-wide student reads retain their existing policy. Selected classes
must still belong to that school. The six original search/answer cases reproduced
200 responses before the repair; all now withhold the synthetic evidence after a
separate database transaction changes caller grants. Two cleanup-revocation cases
also pass. The 50-case catalog/API/cleanup regression suite and the final 21-case
revocation/client suite pass with real PostgreSQL; Black, Ruff and the targeted
permissions type check pass. A Docker interruption invalidated an intermediate
run; the final eight revocation cases were rerun successfully. Full authenticated
production consumer proof remains a separate release requirement.
