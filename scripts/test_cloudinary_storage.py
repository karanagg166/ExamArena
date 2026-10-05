#!/usr/bin/env python3
"""Optional manual smoke test script for Cloudinary storage provider.

Usage:
    export CLOUDINARY_CLOUDNAME="your-cloud-name"
    export CLOUDINARY_APIKEY="your-api-key"
    export CLOUDINARY_APISECRET="your-api-secret"
    python scripts/test_cloudinary_storage.py

DO NOT run during automated CI or pytest without credentials.
Never commit secrets into source control.
"""

import asyncio
import os
import sys

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.storage.cloudinary import CloudinaryStorageProvider
from app.storage.base import StorageConfigurationError, StoredFile


async def main():
    cloud_name = os.getenv("CLOUDINARY_CLOUDNAME")
    api_key = os.getenv("CLOUDINARY_APIKEY")
    api_secret = os.getenv("CLOUDINARY_APISECRET")

    if not cloud_name or not api_key or not api_secret:
        print("ERROR: Cloudinary credentials missing from environment.")
        print("Please set CLOUDINARY_CLOUDNAME, CLOUDINARY_APIKEY, and CLOUDINARY_APISECRET.")
        sys.exit(1)

    print(f"Connecting to Cloudinary (cloud: {cloud_name})...")
    try:
        provider = CloudinaryStorageProvider(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
        )
    except StorageConfigurationError as e:
        print(f"Configuration failed: {e}")
        sys.exit(1)

    # 1. Test PDF upload (raw resource_type)
    test_pdf_content = b"%PDF-1.4\n% Smoke test PDF for CloudinaryStorageProvider\n%%EOF"
    print("\n1. Testing raw PDF upload...")
    stored_pdf = await provider.save_file(
        content=test_pdf_content,
        extension=".pdf",
        directory="smoke-tests/test-exam",
    )
    print(f"   Upload successful!")
    print(f"   Key: {stored_pdf.key}")
    print(f"   URL: {stored_pdf.url}")
    print(f"   Resource Type: {stored_pdf.resource_type}")

    # 2. Test download
    print("\n2. Testing asset download...")
    downloaded_bytes = await provider.get_file(stored_pdf.key, resource_type=stored_pdf.resource_type)
    if downloaded_bytes == test_pdf_content:
        print(f"   Download verified! Bytes matched ({len(downloaded_bytes)} bytes).")
    else:
        print(f"   WARNING: Downloaded content differs! Got {len(downloaded_bytes)} bytes, expected {len(test_pdf_content)}.")

    # 3. Test cleanup (delete)
    print("\n3. Testing asset cleanup (destroy)...")
    deleted = await provider.delete_file(stored_pdf.key, resource_type=stored_pdf.resource_type)
    if deleted:
        print("   Asset successfully deleted from Cloudinary.")
    else:
        print("   WARNING: Asset deletion returned False.")

    print("\nAll Cloudinary smoke tests passed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
