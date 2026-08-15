import asyncio
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from sqlalchemy import update

import app.core.database as db
from app.core.models import User
from app.core.security import hash_password


async def reset_all_passwords():
    new_hashed = hash_password("karan166")
    async with db.AsyncSessionLocal() as session:
        try:
            stmt = update(User).values(password=new_hashed)
            result = await session.execute(stmt)
            await session.commit()
            print(
                f"Successfully updated passwords for {result.rowcount} users to 'karan166'."
            )
        except Exception as e:
            print(f"Error resetting passwords: {e}")
        finally:
            await db.close_db()


if __name__ == "__main__":
    asyncio.run(reset_all_passwords())
