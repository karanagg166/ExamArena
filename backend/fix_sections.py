import asyncio

from sqlalchemy import text

import app.core.database as db


async def main() -> None:
    async with db.get_session() as session:
        await session.execute(
            text("UPDATE \"Question\" SET section = 'General' WHERE section IS NULL;")
        )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(main())
