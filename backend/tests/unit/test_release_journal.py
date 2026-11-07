"""Only signed synthetic provenance can authorize release cleanup."""

import json
import os
import stat
import uuid

import pytest

from app.maintenance.release_journal import Journal, owned_title, title_for

KEY = "public-synthetic-course-journal-test-key-001"


def test_signed_title_requires_owner_and_valid_scope():
    title = title_for(KEY, uuid.uuid4().hex, "other-a")
    assert owned_title(KEY, title) == "other-a"
    assert owned_title("other-public-synthetic-owner-key-001", title) is None
    assert owned_title(KEY, title + "x") is None
    assert owned_title(KEY, "somebody else's PDF") is None


def test_journal_is_private_and_preserves_completed_receipts(tmp_path):
    path = tmp_path / "receipt"
    row = str(uuid.uuid4())
    title = title_for(KEY, uuid.uuid4().hex, "a")
    journal = Journal(path, KEY)
    journal.add(row, "a", title)
    pending = tmp_path / "pending"
    pending.write_bytes(path.read_bytes())
    journal.complete(row)
    restored = Journal(path, KEY)
    restored.import_path(pending)
    assert restored.entries[row]["complete"] is True
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    # If metadata is live again, discovery requires deletion verification again.
    restored.add(row, "a", title)
    assert restored.entries[row]["complete"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", str(uuid.uuid4())),
        ("label", "b"),
        ("complete", True),
        ("signature", "0" * 64),
    ],
)
def test_tampered_receipt_cannot_authorize_cleanup(tmp_path, field, value):
    path = tmp_path / "receipt"
    journal = Journal(path, KEY)
    journal.add(str(uuid.uuid4()), "a", title_for(KEY, uuid.uuid4().hex, "a"))
    data = json.loads(path.read_text())
    data["entries"][0][field] = value
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        Journal(path, KEY)


def test_foreign_owner_and_unsafe_local_file_are_rejected(tmp_path):
    path = tmp_path / "receipt"
    Journal(path, KEY).save()
    with pytest.raises(ValueError):
        Journal(path, "other-public-synthetic-owner-key-001")
    path.chmod(0o644)
    with pytest.raises(ValueError):
        Journal(path, KEY)
    path.chmod(0o600)
    linked = tmp_path / "linked"
    linked.symlink_to(path)
    with pytest.raises(OSError):
        Journal(linked, KEY)
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo, 0o600)
    with pytest.raises(ValueError):
        Journal(fifo, KEY)
