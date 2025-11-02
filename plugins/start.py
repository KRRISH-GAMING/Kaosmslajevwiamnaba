import traceback, asyncio, re, time as pytime
from datetime import datetime, timedelta
from pyrogram import *
from pyrogram.types import *
from pyrogram.errors import *
from pyrogram.errors.exceptions.bad_request_400 import *
from plugins.config import *
from plugins.database import *
from plugins.helper import *

PAYMENT_CACHE = {}
PENDING_TXN = {}

LOG_TEXT = """<b><u>#NewUser</u></b>
    
Id - <code>{}</code>

Name - {}

Username - {}"""

broadcast_cancel = False

START_TIME = pytime.time()

@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    try:
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        mention = message.from_user.mention
        username = message.from_user.username

        username_text = f"@{username}" if username else "None"

        if not await db.is_user_exist(user_id):
            await db.add_user(user_id, first_name)
            await safe_action(
                client.send_message,
                LOG_CHANNEL,
                LOG_TEXT.format(user_id, mention, username_text)
            )

        buttons = [
            [InlineKeyboardButton("🌟 Our Premium Plans", callback_data="x1")],
            #[InlineKeyboardButton("📊 Check Your Subscription", callback_data="x2")],
            [InlineKeyboardButton("♈ How To Buy Premium", url="https://t.me/Open_Shorten_Link_Tutorial/13")],
            [InlineKeyboardButton("🆘 Help & Support", callback_data="x3")]
        ]

        return await safe_action(
            message.reply_text,
            text=(
                "Hello👋 Members"
                "\n\n🎖️ Welcome To The Premium Channel Subscription Bot"
                "\n\nHere you can buy premium channels through our bot and get exclusive content instantly!"
                "\n\n💳 Make payment and get your premium link right now in seconds."
                "\n\n👇🏻 Please choose an option below:"
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        await safe_action(
            client.send_message,
            LOG_CHANNEL,
            f"⚠️ Start Handler Error:\n\n<code>{e}</code>\n\nTraceback:\n<code>{traceback.format_exc()}</code>."
        )
        print(f"⚠️ Start Handler Error: {e}")
        print(traceback.format_exc())

@Client.on_message(filters.command("broadcast") & filters.private & filters.user(ADMINS))
async def broadcast(client, message):
    global broadcast_cancel
    broadcast_cancel = False
    try:
        if message.reply_to_message:
            b_msg = message.reply_to_message
        else:
            b_msg = await safe_action(client.ask,
                message.chat.id,
                "📩 Send the message to broadcast\n\n/cancel to stop.",
            )

            if b_msg.text and b_msg.text.lower() == "/cancel":
                return await safe_action(message.reply_text, "🚫 Broadcast cancelled.")

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Cancel Broadcast", callback_data="cancel_broadcast")]]
        )

        sts = await safe_action(message.reply_text,
            "⏳ Broadcast starting...",
            reply_markup=keyboard,
        )
        start_time = pytime.time()
        total_users = await db.total_users_count()

        done = blocked = deleted = failed = success = 0

        users = await db.get_all_users()
        async for user in users:
            if broadcast_cancel:
                await safe_action(sts.edit_text, "🚫 Broadcast cancelled by admin.")
                print("🛑 Broadcast cancelled mid-way.")
                return
            try:
                if "id" in user:
                    pti, sh = await broadcast_messagesx(int(user["id"]), b_msg)
                    if pti:
                        success += 1
                    else:
                        if sh == "Blocked":
                            blocked += 1
                        elif sh == "Deleted":
                            deleted += 1
                        else:
                            failed += 1
                    done += 1

                    if done % 10 == 0 or done == total_users:
                        progress = broadcast_progress_bar(done, total_users)
                        percent = (done / total_users) * 100
                        elapsed = pytime.time() - start_time
                        speed = done / elapsed if elapsed > 0 else 0
                        remaining = total_users - done
                        eta = timedelta(seconds=int(remaining / speed)) if speed > 0 else "∞"

                        try:
                            await safe_action(sts.edit, f"""
📢 <b>Broadcast in Progress...</b>

{progress}

👥 Total Users: {total_users}
✅ Success: {success}
🚫 Blocked: {blocked}
❌ Deleted: {deleted}
⚠️ Failed: {failed}

⏳ ETA: {eta}
⚡ Speed: {speed:.2f} users/sec
""", reply_markup=keyboard)
                        except:
                            pass
                else:
                    done += 1
                    failed += 1
            except Exception:
                failed += 1
                done += 1
                continue

        time_taken = timedelta(seconds=int(pytime.time() - start_time))
        final_progress = broadcast_progress_bar(total_users, total_users)
        final_text = f"""
✅ <b>Broadcast Completed</b> ✅

⏱ Duration: {time_taken}
👥 Total Users: {total_users}

📊 Results:
✅ Success: {success} ({(success/total_users)*100:.1f}%)
🚫 Blocked: {blocked} ({(blocked/total_users)*100:.1f}%)
❌ Deleted: {deleted} ({(deleted/total_users)*100:.1f}%)
⚠️ Failed: {failed} ({(failed/total_users)*100:.1f}%)

━━━━━━━━━━━━━━━━━━━━━━
{final_progress} 100%
━━━━━━━━━━━━━━━━━━━━━━

⚡ Speed: {speed:.2f} users/sec
"""
        await safe_action(sts.edit, final_text)
    except Exception as e:
        await safe_action(client.send_message,
            LOG_CHANNEL,
            f"⚠️ Broadcast Error:\n\n<code>{e}</code>\n\nTraceback:\n<code>{traceback.format_exc()}</code>."
        )
        print(f"⚠️ Broadcast Error: {e}")
        print(traceback.format_exc())

@Client.on_message(filters.command("stats") & filters.private & filters.user(ADMINS))
async def stats(client, message):
    try:
        me = await get_me_safe(client)
        if not me:
            return

        username = me.username
        users_count = await db.total_users_count()

        uptime = str(timedelta(seconds=int(pytime.time() - START_TIME)))

        await safe_action(message.reply_text,
            f"📊 Status for @{username}\n\n"
            f"👤 Users: {users_count}\n"
            f"⏱ Uptime: {uptime}\n",
        )
    except Exception as e:
        await safe_action(client.send_message,
            LOG_CHANNEL,
            f"⚠️ Stats Error:\n\n<code>{e}</code>\n\nTraceback:\n<code>{traceback.format_exc()}</code>."
        )
        print(f"⚠️ Stats Error: {e}")
        print(traceback.format_exc())

PLAN_CHANNEL_MAP = {
    # Desi/Onlyfans
    "y1p1": -1003246924678,
    "y1p2": -1003246924678,
    "y1p3": -1003246924678,
    "y1p4": -1003246924678,

    # Cp/Rp
    "y2p1": -1003238391861,
    "y2p2": -1003238391861,
    "y2p3": -1003238391861,
    "y2p4": -1003238391861,

    # Mega Collection
    "y3p1": -1003130577319,
    "y3p2": -1003130577319,
    "y3p3": -1003130577319,
    "y3p4": -1003130577319,

}

@Client.on_callback_query()
async def callback(client, query):
    try:
        me = await get_me_safe(client)
        if not me:
            return

        user_id = query.from_user.id
        data = query.data

        # Start
        if data == "x0":
            buttons = [
                [InlineKeyboardButton("🌟 Our Premium Plans", callback_data="x1")],
                #[InlineKeyboardButton("📊 Check Your Subscription", callback_data="x2")],
                [InlineKeyboardButton("♈ How To Buy Premium", url="https://t.me/Open_Shorten_Link_Tutorial/13")],
                [InlineKeyboardButton("🆘 Help & Support", callback_data="x3")]
            ]
            await safe_action(
                query.message.edit_text,
                text=(
                    "Hello👋 Members"
                    "\n\n🎖️ Welcome To The Premium Channel Subscription Bot"
                    "\n\nHere you can buy premium channels through our bot and get exclusive content instantly!"
                    "\n\n💳 Make payment and get your premium link right now in seconds."
                    "\n\n👇🏻 Please choose an option below:"
                ),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await safe_action(query.answer)

        # Plans
        elif data == "x1":
            buttons = [
                [InlineKeyboardButton("🎬 Mixed Collection", callback_data="y1")],
                [InlineKeyboardButton("🕵️‍♂️ Cp/Rp Collection", callback_data="y2")],
                [InlineKeyboardButton("🚀 Mega Collection", callback_data="y3")],
                [InlineKeyboardButton("🔙 Back", callback_data="x0")]
            ]
            await safe_action(
                query.message.edit_text,
                text=(
                    "📋 Choose a plan below:"
                    "\n\n🔽 Select which premium channel plan you want to buy:"
                ),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await safe_action(query.answer)

        # Demo & Price
        elif data == "y1":
            buttons = [
                [InlineKeyboardButton("🔥 Preview", url="https://t.me/XclusivePreviewBot?start=BATCH-NjhmZDFjZTczMjdkMTAyNjk2YjIxNzAz")],
                [InlineKeyboardButton("💰 ₹100 - 1️⃣ Month", callback_data="y1p1")],
                [InlineKeyboardButton("💰 ₹200 - 3️⃣ Month", callback_data="y1p2")],
                [InlineKeyboardButton("💰 ₹300 - 6️⃣ Month", callback_data="y1p3")],
                [InlineKeyboardButton("💰 ₹500 - Lifetime", callback_data="y1p4")],
                [InlineKeyboardButton("🔙 Back", callback_data="x1")]
            ]
            await safe_action(
                query.message.edit_text,
                text=(
                    "Available Plans👇🏻"
                    "\n•1 Month: ₹100"
                    "\n•3 Months: ₹200"
                    "\n•6 Months: ₹300"
                    "\n•Lifetime: ₹500"
                    "\n\nSelect A Plan To Subscribe Or Click 'Demo' To See A Preview📌"
                ),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await safe_action(query.answer)

        # Payment menu when a price is selected
        elif data.startswith("y1p"):
            price_map = {
                "y1p1": ("₹100", "1️⃣ Month"),
                "y1p2": ("₹200", "3️⃣ Month"),
                "y1p3": ("₹300", "6️⃣ Month"),
                "y1p4": ("₹500", "Lifetime")
            }

            price, duration = price_map[data]

            buttons = [
                [InlineKeyboardButton("✅ Payment Done", callback_data=f"paid1_{data}")],
                [InlineKeyboardButton("🔙 Back", callback_data="y1")]
            ]

            upi_id = "krrishmehta@airtel"
            upi_name = "KM Membership Bot"
            qr_image = generate_upi_qr(upi_id, upi_name, price)

            caption = (
                f"🎬 Mixed Collection\n\n"
                f"Selected Plan: {duration}\n"
                f"Price: {price}\n"
                f"UPI ID: `{upi_id}` \n\n"
                f"Once you pay, click ✅ Payment Done."
            )

            await safe_action(query.message.delete)

            await safe_action(
                client.send_photo,
                chat_id=query.message.chat.id,
                photo=qr_image,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.MARKDOWN
            )
            await safe_action(query.answer)

        # User clicked Payment Done
        elif data.startswith("paid1_"):
            plan_key = data.replace("paid1_", "")
            plan_map = {
                "y1p1": ("₹100", "1️⃣ Month"),
                "y1p2": ("₹200", "3️⃣ Month"),
                "y1p3": ("₹300", "6️⃣ Month"),
                "y1p4": ("₹500", "Lifetime")
            }

            if plan_key not in plan_map:
                return await query.message.edit_text("⚠️ Invalid plan key.")

            price, duration = plan_map[plan_key]
            amount_expected = int(price.replace("₹", ""))

            await safe_action(
                query.message.edit_text,
                text=(
                    f"🔍 Checking payment status...\n\n"
                    f"Feature: {duration}\n"
                    f"💰 Amount: ₹{amount_expected}\n"
                    f"⚡ Please wait while we verify your transaction."
                ),
                parse_mode=enums.ParseMode.MARKDOWN
            )

            now = datetime.utcnow()

            matched_payment = None
            for txn in PAYMENT_CACHE.values():
                if (txn["amount"] == amount_expected and (now - txn["time"]).seconds < 300 and not txn.get("used_for")):
                    matched_payment = txn
                    break

            if matched_payment:
                matched_payment["used_for"] = plan_key

                PENDING_TXN[query.from_user.id] = {
                    "duration": duration,
                    "amount_expected": amount_expected,
                    "txn_expected": matched_payment["txn_id"],
                    "callback_message": query.message,
                    "plan_key": plan_key
                }

                await safe_action(
                    query.message.edit_text,
                    f"✅ Payment detected for ₹{amount_expected}!\n\n"
                    "Please reply with your **Transaction ID (Txn ID)** to confirm your payment.",
                    parse_mode=enums.ParseMode.MARKDOWN
                )
            else:
                await safe_action(
                    query.message.edit_text,
                    f"❌ No new payment found for ₹{amount_expected}.\n\n"
                    "Make sure your transaction is completed and try again after 1 minute.",
                    parse_mode=enums.ParseMode.MARKDOWN
                )
            await safe_action(query.answer)

        # Demo & Price
        elif data == "y2":
            buttons = [
                [InlineKeyboardButton("🔥 Preview", url="https://t.me/XclusivePreviewBot?start=BATCH-NjhmZDFlMjgzMjdkMTAyNjk2YjIxNzE4")],
                [InlineKeyboardButton("💰 ₹200 - 1️⃣ Month", callback_data="y2p1")],
                [InlineKeyboardButton("💰 ₹400 - 3️⃣ Months", callback_data="y2p2")],
                [InlineKeyboardButton("💰 ₹600 - 6️⃣ Months", callback_data="y2p3")],
                [InlineKeyboardButton("💰 ₹1000 - Lifetimes", callback_data="y2p4")],
                [InlineKeyboardButton("🔙 Back", callback_data="x1")]
            ]
            await safe_action(
                query.message.edit_text,
                text=(
                    "Available Plans👇🏻"
                    "\n•1 Month: ₹200"
                    "\n•3 Months: ₹400"
                    "\n•6 Months: ₹600"
                    "\n•Lifetime: ₹1000"
                    "\n\nSelect A Plan To Subscribe Or Click 'Demo' To See A Preview📌"
                ),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await safe_action(query.answer)

        # Payment menu when a price is selected
        elif data.startswith("y2p"):
            price_map = {
                "y2p1": ("₹200", "1️⃣ Month"),
                "y2p2": ("₹400", "3️⃣ Month"),
                "y2p3": ("₹600", "6️⃣ Month"),
                "y2p4": ("₹1000", "Lifetime")
            }

            price, duration = price_map[data]

            buttons = [
                [InlineKeyboardButton("✅ Payment Done", callback_data=f"paid2_{data}")],
                [InlineKeyboardButton("🔙 Back", callback_data="y2")]
            ]

            upi_id = "krrishmehta@airtel"
            upi_name = "KM Membership Bot"
            qr_image = generate_upi_qr(upi_id, upi_name, price)

            caption = (
                f"🕵️‍♂️ Cp/Rp Collection\n\n"
                f"Selected Plan: {duration}\n"
                f"Price: {price}\n"
                f"UPI ID: `{upi_id}` \n\n"
                f"Once you pay, click ✅ Payment Done."
            )

            await safe_action(query.message.delete)

            await safe_action(
                client.send_photo,
                chat_id=query.message.chat.id,
                photo=qr_image,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.MARKDOWN
            )
            await safe_action(query.answer)

        # User clicked Payment Done
        elif data.startswith("paid2_"):
            plan_key = data.replace("paid2_", "")
            plan_map = {
                "y2p1": ("₹200", "1️⃣ Month"),
                "y2p2": ("₹400", "3️⃣ Month"),
                "y2p3": ("₹600", "6️⃣ Month"),
                "y2p4": ("₹1000", "Lifetime")
            }

            if plan_key not in plan_map:
                return await query.message.edit_text("⚠️ Invalid plan key.")

            price, duration = plan_map[plan_key]
            amount_expected = int(price.replace("₹", ""))

            await safe_action(
                query.message.edit_text,
                text=(
                    f"🔍 Checking payment status...\n\n"
                    f"Feature: {duration}\n"
                    f"💰 Amount: ₹{amount_expected}\n"
                    f"⚡ Please wait while we verify your transaction."
                ),
                parse_mode=enums.ParseMode.MARKDOWN
            )

            now = datetime.utcnow()

            matched_payment = None
            for txn in PAYMENT_CACHE.values():
                if (txn["amount"] == amount_expected and (now - txn["time"]).seconds < 300 and not txn.get("used_for")):
                    matched_payment = txn
                    break

            if matched_payment:
                matched_payment["used_for"] = plan_key

                PENDING_TXN[query.from_user.id] = {
                    "duration": duration,
                    "amount_expected": amount_expected,
                    "txn_expected": matched_payment["txn_id"],
                    "callback_message": query.message,
                    "plan_key": plan_key
                }

                await safe_action(
                    query.message.edit_text,
                    f"✅ Payment detected for ₹{amount_expected}!\n\n"
                    "Please reply with your **Transaction ID (Txn ID)** to confirm your payment.",
                    parse_mode=enums.ParseMode.MARKDOWN
                )
            else:
                await safe_action(
                    query.message.edit_text,
                    f"❌ No new payment found for ₹{amount_expected}.\n\n"
                    "Make sure your transaction is completed and try again after 1 minute.",
                    parse_mode=enums.ParseMode.MARKDOWN
                )
            await safe_action(query.answer)

        # Demo & Price
        elif data == "y3":
            buttons = [
                [InlineKeyboardButton("🔥 Preview", url="https://t.me/XclusivePreviewBot?start=BATCH-NjhmZDFlZDIzMjdkMTAyNjk2YjIxNzI0")],
                [InlineKeyboardButton("💰 ₹200 - 1️⃣ Month", callback_data="y3p1")],
                [InlineKeyboardButton("💰 ₹400 - 3️⃣ Month", callback_data="y3p2")],
                [InlineKeyboardButton("💰 ₹600 - 6️⃣ Month", callback_data="y3p3")],
                [InlineKeyboardButton("💰 ₹1000 - Lifetime", callback_data="y3p4")],
                [InlineKeyboardButton("🔙 Back", callback_data="x1")]
            ]
            await safe_action(
                query.message.edit_text,
                text=(
                    "Available Plans👇🏻"
                    "\n•1 Month: ₹200"
                    "\n•3 Months: ₹400"
                    "\n•6 Months: ₹600"
                    "\n•Lifetime: ₹1000"
                    "\n\nSelect A Plan To Subscribe Or Click 'Demo' To See A Preview📌"
                ),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await safe_action(query.answer)

        # Payment menu when a price is selected
        elif data.startswith("y3p"):
            price_map = {
                "y3p1": ("₹200", "1️⃣ Month"),
                "y3p2": ("₹400", "3️⃣ Month"),
                "y3p3": ("₹600", "6️⃣ Month"),
                "y3p4": ("₹1000", "Lifetime")
            }

            price, duration = price_map[data]

            buttons = [
                [InlineKeyboardButton("✅ Payment Done", callback_data=f"paid3_{data}")],
                [InlineKeyboardButton("🔙 Back", callback_data="y3")]
            ]

            upi_id = "krrishmehta@airtel"
            upi_name = "KM Membership Bot"
            qr_image = generate_upi_qr(upi_id, upi_name, price)

            caption = (
                f"🚀 Mega Collection\n\n"
                f"Selected Plan: {duration}\n"
                f"Price: {price}\n"
                f"UPI ID: `{upi_id}` \n\n"
                f"Once you pay, click ✅ Payment Done."
            )

            await safe_action(query.message.delete)

            await safe_action(
                client.send_photo,
                chat_id=query.message.chat.id,
                photo=qr_image,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.MARKDOWN
            )
            await safe_action(query.answer)

        # User clicked Payment Done
        elif data.startswith("paid3_"):
            plan_key = data.replace("paid3_", "")
            plan_map = {
                "y3p1": ("₹200", "1️⃣ Month"),
                "y3p2": ("₹400", "3️⃣ Month"),
                "y3p3": ("₹600", "6️⃣ Month"),
                "y3p4": ("₹1000", "Lifetime")
            }

            if plan_key not in plan_map:
                return await query.message.edit_text("⚠️ Invalid plan key.")

            price, duration = plan_map[plan_key]
            amount_expected = int(price.replace("₹", ""))

            await safe_action(
                query.message.edit_text,
                text=(
                    f"🔍 Checking payment status...\n\n"
                    f"Feature: {duration}\n"
                    f"💰 Amount: ₹{amount_expected}\n"
                    f"⚡ Please wait while we verify your transaction."
                ),
                parse_mode=enums.ParseMode.MARKDOWN
            )

            now = datetime.utcnow()

            matched_payment = None
            for txn in PAYMENT_CACHE.values():
                if (txn["amount"] == amount_expected and (now - txn["time"]).seconds < 300 and not txn.get("used_for")):
                    matched_payment = txn
                    break

            if matched_payment:
                matched_payment["used_for"] = plan_key

                PENDING_TXN[query.from_user.id] = {
                    "duration": duration,
                    "amount_expected": amount_expected,
                    "txn_expected": matched_payment["txn_id"],
                    "callback_message": query.message,
                    "plan_key": plan_key
                }

                await safe_action(
                    query.message.edit_text,
                    f"✅ Payment detected for ₹{amount_expected}!\n\n"
                    "Please reply with your **Transaction ID (Txn ID)** to confirm your payment.",
                    parse_mode=enums.ParseMode.MARKDOWN
                )
            else:
                await safe_action(
                    query.message.edit_text,
                    f"❌ No new payment found for ₹{amount_expected}.\n\n"
                    "Make sure your transaction is completed and try again after 1 minute.",
                    parse_mode=enums.ParseMode.MARKDOWN
                )
            await safe_action(query.answer)

        # Subscription
        elif data == "x2":
            await safe_action(query.answer)

        # Help
        elif data == "x3":
            buttons = [
                [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/PookieManagerBot")],
                [InlineKeyboardButton("🔙 Back", callback_data="x0")]
            ]
            await safe_action(
                query.message.edit_text,
                text=(
                    "💡 Help & Support"
                    "\n\nIf you have any questions or need assistance with your subscription, please contact our admin."
                    "\n\nFor common questions:"
                    "- To Subscribe: Select 'Our Premium Plans' from the main menu"
                    "- To Check Your Subscriptions: Select 'My Paid Subscriptions' from the main menu"
                    "- Payment Issues: Contact our admin directly"
                    "- Access Problems: Contact admin with your subscription details"
                    "- If You Need More Premium: Talk to our support admin"
                    "\n\nOur Support Admin: @admin"
                ),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await safe_action(query.answer)

        else:
            await safe_action(
                client.send_message,
                LOG_CHANNEL,
                f"⚠️ Unknown Callback Data Received:\n\n{data}\n\nUser: {query.from_user.id}\n\nTraceback:\n<code>{traceback.format_exc()}</code>."
            )
            await safe_action(query.answer, "⚠️ Unknown action.", show_alert=True)
    except Exception as e:
        await safe_action(
            client.send_message,
            LOG_CHANNEL,
            f"⚠️ Callback Handler Error:\n\n<code>{e}</code>\n\nTraceback:\n<code>{traceback.format_exc()}</code>."
        )
        print(f"⚠️ Callback Handler Error: {e}")
        print(traceback.format_exc())
        await safe_action(query.answer, "❌ An error occurred. The admin has been notified.", show_alert=True)

@Client.on_message(filters.all)
async def message_capture(client: Client, message: Message):
    try:
        if not message or not message.chat:
            return

        chat = message.chat
        user_id = message.from_user.id if message.from_user else None

        if chat.type == enums.ChatType.PRIVATE and user_id:
            if not (
                user_id in PENDING_TXN
            ):
                return

            # -------------------- CONFIRM TXN ID --------------------
            if user_id in PENDING_TXN:
                try:
                    await safe_action(message.delete)
                except:
                    pass

                new_text = message.text.strip() if message.text else ""

                data = PENDING_TXN[user_id]
                expected_txn = data["txn_expected"]
                duration = data["duration"]
                amount_expected = data["amount_expected"]
                callback_message = data["callback_message"]
                plan_key = data.get("plan_key")

                if new_text == expected_txn:
                    channel_id = PLAN_CHANNEL_MAP.get(plan_key)
                    if not channel_id:
                        await safe_action(
                            callback_message.edit_text,
                            "⚠️ No channel assigned for this plan. Contact admin."
                        )
                        return

                    user = message.from_user
                    await safe_action(
                        client.send_message,
                        ADMINS,
                        f"📢 <b>New Payment Verified</b>\n\n"
                        f"👤 <b>User:</b> {user.mention} (<code>{user.id}</code>)\n"
                        f"💬 <b>Username:</b> @{user.username or 'None'}\n"
                        f"💰 <b>Amount:</b> ₹{amount_expected}\n"
                        f"🕒 <b>Duration:</b> {duration}\n"
                        f"🧾 <b>Txn ID:</b> <code>{expected_txn}</code>\n"
                        f"🎫 <b>Plan:</b> {plan_key}\n"
                        f"🔗 <b>Invite Link:</b> {invite.invite_link}",
                        parse_mode=enums.ParseMode.HTML
                    )

                    invite = await client.create_chat_invite_link(
                        chat_id=channel_id,
                        name=f"Access for {message.from_user.first_name}",
                        expire_date = datetime.utcnow() + timedelta(hours=1),
                        member_limit=1
                    )

                    await safe_action(
                        callback_message.edit_text,
                        f"✅ Payment verified!\n\n"
                        f"👤 User: {user.mention} (<code>{user.id}</code>)\n"
                        f"💬 Username: @{user.username or 'None'}\n"
                        f"💰 Amount: ₹{amount_expected}\n"
                        f"🕒 Duration: {duration}\n"
                        f"🧾 Txn ID: <code>{expected_txn}</code>\n"
                        f"🎫 Plan: {plan_key}\n"
                        f"🎟️ Your personal access link:\n{invite.invite_link}\n\n"
                        f"⚠️ This link will expire automatically after you join.",
                        parse_mode=enums.ParseMode.MARKDOWN
                    )

                    async def revoke_after_join():
                        await asyncio.sleep(60)
                        try:
                            await client.revoke_chat_invite_link(channel_id, invite.invite_link)
                        except Exception:
                            pass

                    asyncio.create_task(revoke_after_join())
                else:
                    await safe_action(
                        callback_message.edit_text,
                        f"❌ Invalid Txn ID.\n"
                        f"Expected: `{expected_txn}`\n"
                        f"Entered: `{new_text}`\n\n"
                        "Please try again or contact admin.",
                        parse_mode=enums.ParseMode.MARKDOWN
                    )

                del PENDING_TXN[user_id]
                return
        elif chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL]:
            if message.chat.id in [PAYMENT_CHANNEL]:

                text = message.text or ""
                if "💰 Airtel Payment Received" not in text:
                    return

                amount_match = re.search(r"Amount:\s*₹([\d.]+)", text)
                txn_match = re.search(r"Txn ID:\s*(\d+)", text)

                if not (amount_match and txn_match):
                    return

                amount = float(amount_match.group(1))
                txn_id = txn_match.group(1)
                txn_time = datetime.utcnow()

                PAYMENT_CACHE[txn_id] = {
                    "amount": amount,
                    "txn_id": txn_id,
                    "time": txn_time
                }

                expired_txns = [
                    old_txn
                    for old_txn, info in PAYMENT_CACHE.items()
                    if (txn_time - info["time"]).seconds > 300
                ]

                for old_txn in expired_txns:
                    del PAYMENT_CACHE[old_txn]
    except Exception as e:
        await safe_action(
            client.send_message,
            LOG_CHANNEL,
            f"⚠️ Clone message_capture Error:\n\n<code>{e}</code>\n\nTraceback:\n<code>{traceback.format_exc()}</code>."
        )
        print(f"⚠️ Clone message_capture Error: {e}")
        print(traceback.format_exc())
