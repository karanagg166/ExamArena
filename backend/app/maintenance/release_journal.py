"""Signed, content-free synthetic document receipts survive interrupted release runs."""

import hashlib
import hmac
import json
import os
import re
import stat
import uuid
from pathlib import Path

LABELS = {"a", "b", "other-a"}
ID_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def signature(key, value):
    return hmac.new(
        key.encode(), ("exam-arena-journey-v1:" + value).encode(), "sha256"
    ).hexdigest()


def title_for(key, run, label):
    if label not in LABELS or not re.fullmatch(r"[0-9a-f]{32}", run):
        raise ValueError("Invalid fixture title identity.")
    value = "EA_SS_V1_" + run + "_" + label
    return value + "_" + signature(key, value)[:24]


def owned_title(key, title):
    match = re.fullmatch(
        r"EA_SS_V1_([0-9a-f]{32})_(a|b|other-a)_([0-9a-f]{24})", title or ""
    )
    if not match:
        return None
    expected = title_for(key, match[1], match[2])
    return match[2] if hmac.compare_digest(title, expected) else None


class Journal:
    def __init__(self, path, key):
        if not isinstance(key, str) or len(key) < 32:
            raise ValueError("A private release ownership key is required.")
        self.path, self.key = Path(path), key
        self.entries = {}
        if self.path.exists() or self.path.is_symlink():
            self.import_path(self.path, private=True)

    def sealed(self, entry):
        raw = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        return {**entry, "signature": signature(self.key, raw)}

    def import_path(self, path, *, private=False):
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, encoding="utf-8") as handle:
            metadata = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_size > 1048576
                or (private and metadata.st_mode & 0o077)
            ):
                raise ValueError("Unsafe fixture receipt file.")
            value = json.load(handle)
        if (
            not isinstance(value, dict)
            or set(value) != {"version", "owner", "entries"}
            or value["version"] != 1
            or value["owner"] != signature(self.key, "owner")
            or not isinstance(value["entries"], list)
            or len(value["entries"]) > 2000
        ):
            raise ValueError("Invalid fixture journal owner or format.")
        for item in value["entries"]:
            if not isinstance(item, dict) or set(item) != {
                "id",
                "label",
                "title",
                "complete",
                "signature",
            }:
                raise ValueError("Invalid fixture receipt.")
            entry = {key: item[key] for key in ("id", "label", "title", "complete")}
            if (
                not isinstance(entry["id"], str)
                or not re.fullmatch(ID_PATTERN, entry["id"])
                or type(entry["complete"]) is not bool
                or entry["label"] not in LABELS
                or entry["label"] != owned_title(self.key, entry["title"])
                or not hmac.compare_digest(
                    item["signature"], self.sealed(entry)["signature"]
                )
            ):
                raise ValueError("Fixture receipt signature or scope mismatch.")
            existing = self.entries.get(entry["id"])
            if existing and any(
                existing[field] != entry[field] for field in ("label", "title")
            ):
                raise ValueError("Conflicting fixture receipt identities.")
            # A later verified-complete receipt takes precedence over an older pending copy.
            if not existing or entry["complete"]:
                self.entries[entry["id"]] = entry

    def save(self):
        if len(self.entries) > 2000:
            raise ValueError(
                "Fixture receipt capacity requires operator reconciliation."
            )
        value = {
            "version": 1,
            "owner": signature(self.key, "owner"),
            "entries": [self.sealed(entry) for entry in self.entries.values()],
        }
        temporary = self.path.with_name(
            self.path.name + "." + uuid.uuid4().hex + ".tmp"
        )
        descriptor = os.open(
            temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(value, handle, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def add(self, identifier, label, title):
        if (
            not isinstance(identifier, str)
            or not re.fullmatch(ID_PATTERN, identifier)
            or label not in LABELS
            or owned_title(self.key, title) != label
        ):
            raise ValueError("Cannot track an unowned fixture.")
        existing = self.entries.get(identifier)
        if existing and (existing["label"] != label or existing["title"] != title):
            raise ValueError("Conflicting fixture receipt.")
        if not existing:
            self.entries[identifier] = {
                "id": identifier,
                "label": label,
                "title": title,
                "complete": False,
            }
        else:
            self.entries[identifier]["complete"] = False
        self.save()

    def complete(self, identifier):
        self.entries[identifier]["complete"] = True
        self.save()
