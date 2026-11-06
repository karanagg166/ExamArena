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
