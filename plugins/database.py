import motor.motor_asyncio
from plugins.config import *

class Database:

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.channels = self.db.channels

    def new_user(self, id, name):
        return dict(id=id, name=name)

    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)

    async def is_user_exist(self, id):
        user = await self.col.find_one({"id": int(id)})
        return bool(user)

    async def total_users_count(self):
        return await self.col.count_documents({})

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({"id": int(user_id)})

    async def get_channels(self):
        data = await self.channels.find_one({"_id": "channels"})
        if not data:
            default_channels = {
                "_id": "channels",
                "x1": -1003246924678,
                "x2": -1003238391861,
                "x3": -1003130577319,
            }
            await self.channels.insert_one(default_channels)
            return default_channels
        return data

    async def update_channel(self, name: str, value: int):
        await self.channels.update_one(
            {"_id": "channels"},
            {"$set": {name.lower(): value}},
            upsert=True,
        )

db = Database(DB_URI, DB_NAME)
