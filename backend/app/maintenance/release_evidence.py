"""Synthetic upload, retrieval, isolation and grounded citation assertions."""

import re
import uuid

from app.maintenance.release_http import ROOT, require, synthetic_pdf
from app.maintenance.release_journal import title_for


def verify_evidence(journey):
    journey.step("upload new synthetic PDFs and poll indexing")
    run, documents, markers = uuid.uuid4().hex, {}, {}
    for label, color in (("a", "violet"), ("b", "teal"), ("other-a", "amber")):
        title = title_for(journey.key, run, label)
        marker = "EA_MARKER_" + uuid.uuid4().hex
        markers[label] = marker
        statement = marker + ": The synthetic atlas color is " + color + "."
        code, value = journey.teacher(label).request(
            "POST",
            ROOT + "/upload",
            fields={
                "title": title,
                "subject": "SCIENCE",
                "class_id": journey.class_id(label),
                "document_type": "TEACHER_NOTES",
            },
            pdf=synthetic_pdf(statement),
            filename=title + ".pdf",
        )
        require(code == 201 and value.get("title") == title, "Synthetic upload failed")
        identifier = value["id"]
        journey.journal.add(identifier, label, title)
        documents[label] = identifier
        deadline = journey.clock() + 240
        while True:
            code, status = journey.teacher(label).request(
                "POST", ROOT + "/" + identifier + "/refresh-status"
            )
            require(
                code == 200 and status.get("material_id") == identifier,
                "Index status unavailable",
            )
            state = status.get("status")
            require(
                state in {"UPLOADED", "PROCESSING", "READY", "FAILED"}
                and state != "FAILED",
                "Synthetic ingestion failed",
            )
            if state == "READY":
                break
            require(journey.clock() < deadline, "Synthetic indexing timed out")
            journey.sleep(2)
    journey.step("authorized marker retrieval and school/class isolation")
    for label, session in (
        ("a", journey.sessions["teacher-a"]),
        ("a", journey.sessions["student-a"]),
        ("b", journey.sessions["student-b"]),
    ):
        code, value = session.request(
            "POST",
            ROOT + "/search",
            value={
                "query": markers[label],
                "subject": "SCIENCE",
                "class_id": journey.class_id(label),
            },
        )
        rows = value.get("results", []) if isinstance(value, dict) else []
        require(
            code == 200
            and rows
            and all(row.get("material_id") == documents[label] for row in rows)
            and any(markers[label] in row.get("text", "") for row in rows),
            "Unique marker retrieval or isolation failed",
        )
    for label in ("b", "other-a"):
        code, _ = journey.sessions["student-a"].request(
            "GET", ROOT + "/" + documents[label]
        )
        require(code == 404, "Foreign evidence metadata disclosed")
        code, value = journey.sessions["student-a"].request(
            "POST",
            ROOT + "/search",
            value={
                "query": markers[label],
                "subject": "SCIENCE",
                "class_id": journey.class_id(label),
            },
        )
        require(code in (403, 404), "Foreign class query was not denied")
        code, value = journey.sessions["student-a"].request(
            "POST",
            ROOT + "/search",
            value={
                "query": markers[label],
                "subject": "SCIENCE",
                "class_id": journey.class_id("a"),
            },
        )
        require(
            code == 200
            and isinstance(value.get("results"), list)
            and all(
                row.get("material_id") != documents[label]
                and markers[label] not in row.get("text", "")
                for row in value["results"]
            ),
            "Foreign evidence returned through authorized collection",
        )
    journey.step("expected grounded answer and supporting page citations")
    code, value = journey.sessions["student-a"].request(
        "POST",
        ROOT + "/answer",
        timeout=65,
        value={
            "query": "For " + markers["a"] + ", what is the synthetic atlas color?",
            "subject": "SCIENCE",
            "classId": journey.class_id("a"),
        },
    )
    require(
        code == 200
        and isinstance(value, dict)
        and "violet" in value.get("answer", "").lower(),
        "Expected grounded answer missing",
    )
    citations = value.get("citations")
    require(isinstance(citations, list) and citations, "Grounded citations missing")
    numbers = set()
    for citation in citations:
        require(
            citation.get("materialId") == documents["a"]
            and citation.get("pageNumber") == 1
            and isinstance(citation.get("chunkId"), str)
            and citation["chunkId"]
            and type(citation.get("citationNumber")) is int
            and citation["citationNumber"] > 0
            and "violet" in citation.get("textSnippet", "").lower()
            and markers["a"] in citation.get("textSnippet", ""),
            "Citation support or permission invalid",
        )
        numbers.add(citation["citationNumber"])
    references = {int(number) for number in re.findall(r"\[(\d+)\]", value["answer"])}
    require(
        references and references.issubset(numbers),
        "Answer citation references invalid",
    )
