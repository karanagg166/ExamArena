"""Private plan/credential files cannot overwrite or follow other local files."""

import os
import stat

import pytest

from app.maintenance.release_bootstrap import private_output, read_private, write_output


def test_private_receipt_roundtrip_never_overwrites(tmp_path):
    path = tmp_path / "plan.json"
    value = {"public_fixture_marker": "synthetic only"}
    with private_output(path) as handle:
        write_output(handle, value)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert read_private(path) == value
    with pytest.raises(FileExistsError):
        private_output(path)
    assert read_private(path) == value


@pytest.mark.parametrize("kind", ["symlink", "world_readable", "oversize", "fifo"])
def test_unsafe_receipts_are_rejected(tmp_path, kind):
    target = tmp_path / "private.json"
    target.write_text("{}")
    target.chmod(0o600)
    path = target
    if kind == "symlink":
        path = tmp_path / "linked.json"
        path.symlink_to(target)
    elif kind == "world_readable":
        target.chmod(0o644)
    elif kind == "oversize":
        target.write_text(" " * 65537)
    else:
        path = tmp_path / "fifo"
        os.mkfifo(path, 0o600)
    with pytest.raises((ValueError, OSError)):
        read_private(path)


def test_credential_output_cannot_follow_symlink(tmp_path):
    original = tmp_path / "original"
    original.write_text("retain")
    linked = tmp_path / "linked"
    linked.symlink_to(original)
    with pytest.raises(OSError):
        private_output(linked)
    assert original.read_text() == "retain"
