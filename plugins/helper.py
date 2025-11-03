import traceback, asyncio, re, qrcode, imaplib, email, pytz
from datetime import datetime
from io import BytesIO
from aiohttp import ClientSession
from pyrogram import *
from pyrogram.types import *
from pyrogram.errors import *
from pyrogram.errors.exceptions.bad_request_400 import *
from plugins.config import *
from plugins.database import *

CLONE_ME = {}

async def set_auto_menu(client):
    try:
        owner_cmds = [
            BotCommand("start", "Check I am alive"),
            BotCommand("resendlinks", "Resend link to users"),
            BotCommand("broadcast", "Broadcast a message to users"),
            BotCommand("stats", "View bot statistics"),
            BotCommand("premiumstats", "View bot premium user statistics"),
        ]
        for admin_id in ADMINS:
            await client.set_bot_commands(owner_cmds, scope=BotCommandScopeChat(chat_id=admin_id))
    except Exception as e:
        await safe_action(client.send_message,
            LOG_CHANNEL,
            f"⚠️ Set Menu Error:\n\n<code>{e}</code>\n\nTraceback:\n<code>{traceback.format_exc()}</code>."
        )
        print(f"⚠️ Set Menu Error: {e}")
        print(traceback.format_exc())

async def safe_action(coro_func, *args, **kwargs):
    while True:
        try:
            return await coro_func(*args, **kwargs)
        except FloodWait as e:
            print(f"⏱ FloodWait: sleeping {e.value} seconds")
            await asyncio.sleep(e.value)
        except UserIsBlocked:
            print(f"⚠️ User blocked the bot. Skipping reply...")
            return
        except Exception as e:
            if "MESSAGE_NOT_MODIFIED" not in str(e) and "MESSAGE_ID_INVALID" not in str(e) and "QUERY_ID_INVALID" not in str(e) and "MESSAGE_DELETE_FORBIDDEN" not in str(e):
                raise
            if "INPUT_USER_DEACTIVATED" in str(e):
                print(f"⚠️ User account is deleted. Skipping...")
                return
            try:
                await coro_func(
                    LOG_CHANNEL,
                    f"⚠️ Error in safe_action:\n\n<code>{e}</code>\n\nTraceback:\n<code>{traceback.format_exc()}</code>."
                )
            except Exception as inner_e:
                print(f"⚠️ Failed logging: {inner_e}")
            print(f"⚠️ Error in safe_action: {e}")
            print(traceback.format_exc())
            return None

async def get_me_safe(client):
    if client in CLONE_ME and CLONE_ME[client]:
        return CLONE_ME[client]

    while True:
        try:
            me = await client.get_me()
            CLONE_ME[client] = me
            return me
        except FloodWait as e:
            print(f"⏳ FloodWait: waiting {e.value}s for get_me()...")
            await asyncio.sleep(e.value)
        except Exception as ex:
            print(f"⚠️ get_me() failed: {ex}")
            return None

def generate_upi_qr(upi_id: str, name: str, amount: float) -> BytesIO:
    upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    bio = BytesIO()
    bio.name = "upi_qr.png"
    img.save(bio, "PNG")
    bio.seek(0)
    return bio

async def fetch_fampay_payments():
    try:
        IMAP_HOST = "imap.gmail.com"
        IMAP_USER = "krrishraj237@gmail.com"
        IMAP_PASS = "ewcz wblx fdgv unpp"

        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(IMAP_USER, IMAP_PASS)

        mail.select("inbox")

        status, email_ids = mail.search(None, '(UNSEEN FROM "no-reply@famapp.in")')

        if status != "OK" or not email_ids or not email_ids[0]:
            return []

        email_list = email_ids[0].split()

        latest_5_emails = email_list[-5:]

        transactions = []
        kolkata_tz = pytz.timezone("Asia/Kolkata")

        for email_id in latest_5_emails:
            status, msg_data = mail.fetch(email_id, "(RFC822)")

            if status != "OK" or not msg_data:
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            email_date = msg["Date"]

            try:
                email_datetime = datetime.strptime(email_date, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError as ve:
                continue

            email_datetime = email_datetime.astimezone(kolkata_tz)

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            if not body:
                continue

            amount_match = re.search(r"₹\s?([\d,.]+)", body)
            if amount_match:
                amount = float(amount_match.group(1).replace(",", ""))
            else:
                amount = None

            txn_match = re.search(r"transaction id\s*[:\-]?\s*(\w+)", body, re.I)
            txn_id = txn_match.group(1) if txn_match else None

            if not amount or not txn_id:
                continue

            txn = {
                "date": email_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "amount": amount,
                "txn_id": txn_id
            }
            transactions.append(txn)

            mail.store(email_id, '+FLAGS', '\\Seen')

        mail.logout()
        return transactions

    except Exception as e:
        await safe_action(
            client.send_message,
            LOG_CHANNEL,
            f"⚠️ IMAP Error:\n<code>{e}</code>\n\nTraceback:\n<code>{traceback.format_exc()}</code>."
        )
        print(f"⚠️ IMAP Error: {e}")
        print(traceback.format_exc())
        return []

def broadcast_progress_bar(done: int, total: int) -> str:
    try:
        progress = done / total if total > 0 else 0
        filled = int(progress * 20)
        empty = 20 - filled
        bar_str = "█" * filled + "░" * empty
        return f"[{bar_str}] {done}/{total}"
    except Exception as e:
        return f"[Error building bar: {e}] {done}/{total}"

async def broadcast_messagesx(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        return False, "Deleted"
    except UserIsBlocked:
        await db.delete_user(int(user_id))
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        return False, "Error"
    except Exception as e:
        return False, f"Error: {str(e)}"
