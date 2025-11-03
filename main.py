from pyrogram import *
from plugins.config import *
from plugins.start import *
from plugins.database import * 
from datetime import datetime
import asyncio

class Bot(Client):

    def __init__(self):
        super().__init__(
            "KM Membership Bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins=dict(root="plugins"),
            workers=50,
            sleep_threshold=10
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.username = '@' + me.username
        await set_auto_menu(self)
        await self.resume_expired_tasks()
        print('Bot Started.')

    async def stop(self, *args):
        await super().stop()
        print('Bot Stopped Bye')

    async def resume_expired_tasks(self):
        async for user in await db.get_active_subscriptions():
            expiry_str = user.get("expiry")
            channel_id = user.get("channel_id")
            user_id = user.get("id")

            if not expiry_str or not channel_id:
                continue

            expiry = datetime.fromisoformat(expiry_str)
            now = datetime.utcnow()
            remaining = (expiry - now).total_seconds()

            if remaining <= 0:
                await db.deactivate_subscription(user_id)
                continue

            async def auto_kick_user_after_restart(uid=user_id, cid=channel_id, exp=expiry):
                await asyncio.sleep((exp - datetime.utcnow()).total_seconds())
                try:
                    await self.kick_chat_member(cid, uid)
                    await self.unban_chat_member(cid, uid)
                    await db.deactivate_subscription(uid)
                    await self.send_message(
                        uid,
                        "⏰ Your premium plan has expired.\n"
                        "You have been removed from the premium channel.",
                        parse_mode=enums.ParseMode.HTML
                    )
                    print(f"✅ Kicked expired user {uid}")
                except Exception as e:
                    print(f"⚠️ Failed to kick {uid}: {e}")

            asyncio.create_task(auto_kick_user_after_restart())

        print("📆 Active subscriptions reloaded and auto-kick tasks scheduled.")

Bot().run()
