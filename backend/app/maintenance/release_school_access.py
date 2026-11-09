"""Production permission checks use only exact, signed synthetic record IDs."""

from app.maintenance.release_http import require


def verify_private_school_records(journey):
    journey.step("private synthetic student records and school isolation")
    for school in ("a", "b"):
        other = "b" if school == "a" else "a"
        own_id = journey.identity["accounts"]["student-" + school]["profile_id"]
        other_id = journey.identity["accounts"]["student-" + other]["profile_id"]
        for role in ("student", "teacher"):
            session = journey.sessions[role + "-" + school]
            own = "/api/v1/students/" + own_id
            foreign = "/api/v1/students/" + other_id
            code, value = session.request("GET", own, timeout=30)
            require(
                code == 200 and value.get("id") == own_id,
                "Authorized student profile unavailable",
            )
            code, _ = session.request("GET", foreign, timeout=30)
            require(code in (403, 404), "Foreign student profile was accessible")
            code, value = session.request("GET", own + "/exams", timeout=30)
            require(
                code == 200 and isinstance(value, list),
                "Authorized student history unavailable",
            )
            code, _ = session.request("GET", foreign + "/exams", timeout=30)
            require(code in (403, 404), "Foreign student history was accessible")
        code, _ = journey.sessions["student-" + school].request(
            "GET",
            "/api/v1/classes/" + journey.class_id(school) + "/students",
            timeout=30,
        )
        require(code == 403, "Student could read classmates' private profiles")
