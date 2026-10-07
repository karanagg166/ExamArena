"""Opt-in live integration smoke test against a running Search-Sphere microservice instance.

Must NEVER run in normal CI or automated unit test runs.
Enable only when explicitly requested via:
    RUN_SEARCH_SPHERE_INTEGRATION=1
"""

import asyncio
import os
import uuid
import pytest

from app.core.config import settings
from app.integrations.search_sphere.client import SearchSphereClient

# Tiny minimal valid PDF structure with synthetic test text
SYNTHETIC_PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources <<>> >>
endobj
4 0 obj
<< /Length 72 >>
stream
BT
/F1 12 Tf
100 700 Td
(ExamArena SearchSphere Synthetic Integration Quantum Dynamics) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000216 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
338
%%EOF"""


@pytest.mark.asyncio
async def test_live_search_sphere_synthetic_smoke():
    if os.getenv("RUN_SEARCH_SPHERE_INTEGRATION") != "1":
        pytest.skip(
            "Opt-in live Search-Sphere integration smoke test skipped. "
            "Set RUN_SEARCH_SPHERE_INTEGRATION=1 with a running Search-Sphere service to run."
        )

    base_url = settings.SEARCH_SPHERE_URL or "http://localhost:8000"
    api_key = settings.SEARCH_SPHERE_API_KEY
    if not api_key:
        pytest.skip("SEARCH_SPHERE_API_KEY is not configured; skipping live smoke test.")

    test_run_id = uuid.uuid4().hex[:8]
    tenant_id = f"school_synthetic_{test_run_id}"
    collection_id = f"coll_smoke_{test_run_id}"
    external_doc_id = f"doc_smoke_{test_run_id}"

    client = SearchSphereClient(
        base_url=base_url,
        api_key=api_key,
        client_id="exam_arena",
        timeout_seconds=15.0,
    )

    try:
        # 1. Ensure test collection
        coll = await client.ensure_collection(
            collection_id=collection_id,
            name=f"Synthetic Smoke Collection {test_run_id}",
            description="Automated synthetic smoke test for ExamArena integration",
            tenant_id=tenant_id,
        )
        assert coll["collection_id"] == collection_id

        # 2. Upload synthetic PDF bytes
        upload_res = await client.upload_file(
            file_bytes=SYNTHETIC_PDF_BYTES,
            filename=f"synthetic_quantum_{test_run_id}.pdf",
            content_type="application/pdf",
            document_id=external_doc_id,
            collection_id=collection_id,
            tenant_id=tenant_id,
        )
        assert "storage_key" in upload_res
        storage_key = upload_res["storage_key"]

        # 3. Register document
        doc_res = await client.register_document(
            external_document_id=external_doc_id,
            storage_key=storage_key,
            file_name=f"synthetic_quantum_{test_run_id}.pdf",
            mime_type="application/pdf",
            file_size=len(SYNTHETIC_PDF_BYTES),
            collection_id=collection_id,
            owner_subject_id=f"user_test_{test_run_id}",
            document_type="TEXTBOOK",
            metadata={"test_run": test_run_id, "category": "smoke"},
            tenant_id=tenant_id,
        )
        assert "id" in doc_res
        doc_id = doc_res["id"]

        # 4. Poll until READY with bounded timeout (up to 30s)
        max_retries = 15
        poll_interval = 2.0
        final_status = "QUEUED"
        last_info: dict = {}
        for _ in range(max_retries):
            last_info = await client.get_document(document_id=doc_id, tenant_id=tenant_id)
            final_status = last_info.get("status", "QUEUED")
            if final_status in ("READY", "FAILED"):
                break
            await asyncio.sleep(poll_interval)

        if final_status == "FAILED":
            error_detail = last_info.get("processing_error") or "indexing failure"
            pytest.fail(
                f"Search-Sphere document indexing failed for document_id={doc_id} "
                f"in collection={collection_id}: {error_detail}"
            )
        elif final_status != "READY":
            pytest.fail(
                f"Search-Sphere indexing timed out before reaching READY status. "
                f"Final status for document_id={doc_id}: {final_status}"
            )

        assert final_status == "READY"

        # 5. Execute semantic search (MUST execute after READY)
        search_res = await client.search(
            query="Quantum Dynamics",
            collection_id=collection_id,
            limit=3,
            tenant_id=tenant_id,
        )
        assert search_res["total"] >= 1
        results = search_res.get("results", [])
        assert len(results) >= 1

        # Verify the uploaded synthetic document is returned
        matching_results = [
            r for r in results
            if r.get("document_id") in (external_doc_id, doc_id)
        ]
        assert len(matching_results) >= 1, (
            f"Expected synthetic document {external_doc_id} in search results, got: {results}"
        )

        # Expected synthetic text is present
        assert any(
            "Quantum Dynamics" in r.get("text", "") or "Synthetic Integration" in r.get("text", "")
            for r in matching_results
        ), f"Expected synthetic text not found in matching document chunks: {matching_results}"

        # Collection scope matches
        for r in results:
            if r.get("collection_id"):
                assert r.get("collection_id") == collection_id

        # 6. Call grounded answer endpoint (Phase 5 live verification)
        # Ask question answerable only from synthetic text
        grounded_res = await client.generate_answer(
            query="What quantum concept is discussed in the synthetic material?",
            tenant_id=tenant_id,
            collection_id=collection_id,
            limit=3,
        )
        assert grounded_res.get("answer") is not None
        assert len(grounded_res.get("answer", "").strip()) > 0
        assert grounded_res.get("citations") is not None
        citations = grounded_res.get("citations", [])
        assert len(citations) >= 1, f"Expected at least one citation, got: {grounded_res}"
        assert any(
            c.get("document_id") in (external_doc_id, doc_id)
            for c in citations
        ), f"Expected citation pointing to synthetic document {external_doc_id}, got: {citations}"

        # Ask unrelated question and verify no-evidence behavior
        unrelated_res = await client.generate_answer(
            query="What is the authentic recipe for Italian tiramisu with mascarpone?",
            tenant_id=tenant_id,
            collection_id=collection_id,
            limit=3,
        )
        unrelated_answer = unrelated_res.get("answer", "")
        unrelated_citations = unrelated_res.get("citations", [])
        assert (
            len(unrelated_citations) == 0
            or "couldn't find" in unrelated_answer.lower()
            or "not contain enough information" in unrelated_answer.lower()
            or "insufficient" in unrelated_answer.lower()
        ), f"Expected no-evidence behavior for unrelated query, got answer: {unrelated_answer}, citations: {unrelated_citations}"

        # 7. Delete document
        deleted = await client.delete_document(document_id=doc_id, tenant_id=tenant_id)
        assert deleted is True

    finally:
        # 8. Cleanup collection using public client method
        try:
            await client.delete_collection(collection_id=collection_id, tenant_id=tenant_id)
        except Exception:
            pass
