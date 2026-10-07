"""Unit tests for Search-Sphere identifier mapping and normalization."""

import pytest
from app.core.models import Subject
from app.integrations.search_sphere.identifiers import (
    build_client_id,
    build_collection_id,
    build_external_document_id,
    build_owner_subject_id,
    build_tenant_id,
    parse_tenant_school_id,
    validate_identifier_token,
)


def test_validate_identifier_token():
    assert validate_identifier_token("valid-id_123.abc:test", "test_field") == "valid-id_123.abc:test"

    with pytest.raises(ValueError, match="cannot be empty"):
        validate_identifier_token("   ", "empty_field")

    with pytest.raises(ValueError, match="Invalid characters"):
        validate_identifier_token("invalid/slash", "bad_field")

    with pytest.raises(ValueError, match="Invalid characters"):
        validate_identifier_token("spaces not allowed", "bad_field")


def test_build_client_id():
    cid = build_client_id()
    assert cid == "exam_arena"


def test_build_tenant_id():
    assert build_tenant_id("sch_001") == "school_sch_001"
    assert build_tenant_id("cbse-delhi-99") == "school_cbse-delhi-99"

    with pytest.raises(ValueError):
        build_tenant_id("")


def test_parse_tenant_school_id():
    assert parse_tenant_school_id("school_sch_001") == "sch_001"
    assert parse_tenant_school_id("raw_tenant") == "raw_tenant"


def test_build_collection_id_subject_only():
    assert build_collection_id(Subject.SCIENCE) == "subject_science"
    assert build_collection_id(Subject.MATHS) == "subject_maths"
    assert build_collection_id("LITERATURE") == "subject_literature"


def test_build_collection_id_with_class():
    coll = build_collection_id(Subject.SCIENCE, class_id="cls_10a")
    assert coll == "class_cls_10a_subject_science"

    coll_math = build_collection_id(Subject.MATHS, class_id="cls_12b")
    assert coll_math == "class_cls_12b_subject_maths"


def test_build_owner_subject_id():
    assert build_owner_subject_id("usr_teacher_10") == "user_usr_teacher_10"

    with pytest.raises(ValueError):
        build_owner_subject_id("")


def test_build_external_document_id():
    assert build_external_document_id("mat_doc_555") == "mat_doc_555"

    with pytest.raises(ValueError):
        build_external_document_id("")
