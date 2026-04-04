import asyncio
from prisma import Prisma

async def main() -> None:
    db = Prisma()
    await db.connect()
    # Update where section is null.
    await db.execute_raw('UPDATE "Question" SET section = \'General\' WHERE section IS NULL;')
    await db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
