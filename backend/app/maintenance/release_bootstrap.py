"""Operator-only synthetic school bootstrap; private environment, dry run by default.

Run as python -m app.maintenance.release_bootstrap with PYTHONPATH=backend.
Never pass DATABASE_URL or RELEASE_FIXTURE_KEY on argv.
"""

import argparse
import asyncio
import json
import os
import stat
from pathlib import Path


def read_private(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, encoding="utf-8") as handle:
        metadata = os.fstat(handle.fileno())
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_mode & 0o077
            or metadata.st_size > 65536
        ):
            raise ValueError("Plan must be a private regular file of at most 64 KiB.")
        return json.load(handle)


def private_output(path):
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    return os.fdopen(descriptor, "w", encoding="utf-8")


def write_output(handle, value):
    json.dump(value, handle, indent=2, sort_keys=True)
    handle.flush()
    os.fsync(handle.fileno())


async def run(args):
    if not os.environ.get("DATABASE_URL"):
        raise ValueError("An explicit private DATABASE_URL is required.")
    from app.core.database import AsyncSessionLocal, engine
    from app.maintenance.release_fixtures import (
        apply_plan,
        build_plan,
        credentials,
        digest,
    )

    key = os.environ.get("RELEASE_FIXTURE_KEY", "")
    try:
        if args.apply:
            plan = read_private(args.apply)
            # Reserve a new private file before mutation; never overwrite an old receipt.
            with private_output(args.credentials) as handle:
                result = await apply_plan(AsyncSessionLocal, key, plan, args.digest)
                write_output(handle, credentials(key))
            return result
        plan = await build_plan(AsyncSessionLocal, key)
        with private_output(args.plan) as handle:
            write_output(handle, plan)
        return {
            "mode": "dry_run",
            "state": plan["state"],
            "records": plan["records"],
            "digest": digest(plan),
            "expires_in_seconds": 900,
        }
    finally:
        await engine.dispose()


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--apply", type=Path)
    parser.add_argument("--digest")
    parser.add_argument("--credentials", type=Path)
    args = parser.parse_args()
    if args.apply:
        if args.plan or not args.digest or not args.credentials:
            parser.error(
                "Apply requires --apply, --digest and a new private --credentials file."
            )
    elif not args.plan or args.digest or args.credentials:
        parser.error("Dry run requires only a new private --plan file.")
    return args


if __name__ == "__main__":
    try:
        print(json.dumps(asyncio.run(run(arguments()))))
    except Exception as error:
        raise SystemExit(
            "Synthetic bootstrap failed ("
            + type(error).__name__
            + "); review private configuration and plan."
        ) from None
