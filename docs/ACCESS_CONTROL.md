# Document and student-record access

The November 8, 2026 owner clarification requires these boundaries. Account
ownership and delegated access do not approve sending private data to an AI provider.

| Requirement | Before this repair | Implementation reference / next verification |
| --- | --- | --- |
| Standalone Search Sphere documents and conversations belong to their user | Working in the inspected service; retain ownership checks | Search Sphere document/conversation authorization and scoped PostgreSQL retrieval; existing synthetic release gate |
| Quick-Clinic doctors access only authorized patients | Working in the inspected consumer | Current doctor/patient checks and qualifying appointments; existing synthetic patient isolation gate |
| ExamArena student private profiles and reports are self-only | Partial: individual exam history is self-only, but full profiles are available to classmates and class rosters expose them | `backend/app/students/router.py`, `backend/app/school_class/router.py`; add peer-denial regression cases |
| Teachers access private student records only for classes they teach | Missing: school affiliation alone grants access, including analytics aliases | `backend/app/students/router.py`, `backend/app/analytics/service.py`; use current `TeacherClass` or primary `SchoolClass.teacherId` assignment plus matching school |
| Principals access records only in their own school | Partial: principal linkage is checked inconsistently; some routes allow unrestricted administrator/unknown roles | Require current role, affiliated school, and principal profile linkage; deny missing authority |
| Shared course-material search follows enrollment/teaching scope | Partial: student enrollment enforced; teachers have school-wide access | `backend/app/course_materials/permissions.py`, catalog CRUD and lifecycle routes; separate follow-up PR |
| Private student uploads use subject scope rather than a shared class collection | Missing: `CourseMaterial` models shared teaching resources, not a private student-document owner | Do not place private student reports in shared course-material collections; add a dedicated authorized subject contract before enabling these uploads |
| AI provider eligibility for confidential/medical content | Deliberately restricted | Cohere trial approval for synthetic/public evaluation does not authorize private reports |

First repair: centralize current school/class grants, restrict student-record
lists and profiles, protect class roster/results and analytics aliases, and test
positive self/assigned-teacher/principal access plus peer, other-class,
cross-school, missing-profile and revoked-assignment denial against PostgreSQL.
Keep exam management ownership rules and unreleased-result redaction intact.
No new database tables, dependencies, providers or paid infrastructure are needed.

The same review found self-service role changes, public administrator signup,
and arbitrary-school principal initialization. The repair rejects these elevation
paths. Principal self-service updates cannot move school authority; trusted school
creation retains its internal update schema. A teacher cannot transfer a student
into a class to acquire access. Existing public exam ownership/grading rules are a
separate contract and are not widened by this change.
School ownership (`School.createdBy` with a current principal role) also grants
authority for that school, including the existing onboarding path without a
teacher profile. Revoking all principal access requires removing both school
ownership and any principal/staff linkage; deleting only one independent grant
does not revoke the other.

Local validation: the initial student/class/analytics regression suite passed
92 tests against disposable PostgreSQL. Additional role-escalation and principal
onboarding checks run before merge. These checks use synthetic records and no model
inference. This is code-exposure evidence; it does not establish historical misuse.
