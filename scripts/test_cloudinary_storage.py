#!/usr/bin/env python3
"""Manual-only Cloudinary smoke test using synthetic files.

Run: python scripts/test_cloudinary_storage.py
Loads the repository .env through application settings; never run in CI.
No network operations or application imports occur during pytest collection.
"""

import asyncio
import io
import logging
import os
import struct
import sys
import zlib
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


def synthetic_pdf() -> bytes:
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 72 72] "
        b"/Resources << >> /Contents 4 0 R >>",
        b"<< /Length 0 >>\nstream\nendstream",
    )
    content = b"%PDF-1.4\n"
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(content))
        content += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_offset = len(content)
    content += b"xref\n0 5\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        content += f"{offset:010d} 00000 n \n".encode()
    content += (
        f"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    ).encode()
    return content


def synthetic_png() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data))
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
        + chunk(b"IEND", b"")
    )


async def check_asset(provider, content, extension, resource_type):
    results = dict.fromkeys(("upload", "download", "byte comparison", "delete"), "FAIL")
    stored = None
    try:
        stored = await provider.save_file(content, extension, directory="smoke-tests")
        if (
            stored.provider == "cloudinary"
            and stored.key.startswith("examarena/smoke-tests/")
            and stored.url
            and stored.resource_type == resource_type
        ):
            results["upload"] = "PASS"
        downloaded = await provider.get_file(
            stored.key, resource_type=stored.resource_type
        )
        results["download"] = "PASS"
        results["byte comparison"] = "PASS" if downloaded == content else "FAIL"
    except Exception:
        # Provider exceptions may contain credentials or URLs; report status only.
        pass
    finally:
        if stored is not None:
            for _ in range(3):
                try:
                    if await provider.delete_file(
                        stored.key, resource_type=stored.resource_type
                    ):
                        results["delete"] = "PASS"
                        break
                except Exception:
                    pass
    cleanup_key = stored.key if stored and results["delete"] == "FAIL" else None
    return results, cleanup_key


async def main() -> int:
    configured = False
    results = {
        label: dict.fromkeys(
            ("upload", "download", "byte comparison", "delete"),
            "NOT RUN" if label == "Image" else "FAIL",
        )
        for label in ("PDF", "Image")
    }
    cleanup_keys = []
    # Suppress SDK/provider diagnostics, including exception text and HTTP URLs.
    logging.disable(logging.CRITICAL)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        try:
            root = Path(__file__).resolve().parents[1]
            os.chdir(
                root
            )  # Settings resolves env_file relative to the working directory.
            sys.path.insert(0, str(root / "backend"))
            from app.core.config import settings
            from app.storage.cloudinary import CloudinaryStorageProvider

            configured = bool(
                settings.CLOUDINARY_CLOUDNAME
                and settings.CLOUDINARY_APIKEY
                and settings.CLOUDINARY_APISECRET
            )
            if configured:
                provider = CloudinaryStorageProvider()
                for label, content, extension, resource_type in (
                    ("PDF", synthetic_pdf(), ".pdf", "raw"),
                    ("Image", synthetic_png(), ".png", "image"),
                ):
                    results[label], cleanup_key = await check_asset(
                        provider, content, extension, resource_type
                    )
                    if cleanup_key:
                        cleanup_keys.append(cleanup_key)
        except Exception:
            pass

    print(f"Cloudinary configuration detected: {'yes' if configured else 'no'}")
    for label, checks in results.items():
        print()
        for operation, result in checks.items():
            print(f"{label} {operation}: {result}")
    for key in cleanup_keys:
        print(f"Cleanup required: {key}")
    return int(
        any(
            result != "PASS"
            for checks in results.values()
            for result in checks.values()
        )
    )


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
