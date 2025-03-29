from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

settings = get_settings()

client = None
db = None


async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.transactions.create_index("user_id")
    await db.transactions.create_index("date")
    await db.transactions.create_index("category_id")
    await db.categories.create_index("user_id")
    await db.categories.create_index([("user_id", 1), ("name", 1)], unique=True)
    await db.budgets.create_index("user_id")
    await db.goals.create_index("user_id")


async def close_mongo_connection():
    global client
    if client:
        client.close()


def get_database():
    return db 