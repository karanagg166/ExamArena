"""ExamArena Database Seed CLI Runner.

Executes modular seeding routines from `seeds/` package.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# Ensure backend directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

import app.core.database as db
from seeds import run_all_seeds


async def main() -> None:
    """Initialize DB connection and run modular seed pipeline."""
    async with db.AsyncSessionLocal() as session:
        try:
            await run_all_seeds(session)
        except Exception as err:
            print(f"❌ Error during database seeding: {err}", flush=True)
            import traceback

            traceback.print_exc()
        finally:
            await db.close_db()


if __name__ == "__main__":
    asyncio.run(main())
