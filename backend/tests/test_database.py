import asyncio

from sqlalchemy import text

from app.db.database import engine


async def test_connection():
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))
        print("Database connection successful:", result.scalar())


asyncio.run(test_connection())