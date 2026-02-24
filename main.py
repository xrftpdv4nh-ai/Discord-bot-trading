import discord
from discord.ext import commands
import motor.motor_asyncio
import asyncio
import re
from datetime import datetime, timedelta

from config import (
    BOT_TOKEN,
    MONGO_URL,
    PROBOT_ID,
    PROBOT_RECEIVER_ID,
    PROBOT_FEE_RATE,
    DEPOSIT_TIMEOUT
)

# ===================== MongoDB =====================
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = mongo_client.trono_trade

wallets_collection = db.wallets
pending_collection = db.pending_deposits

# ===================== Intents =====================
intents = discord.Intents.all()  # مهم جدًا لمراقبة رسائل ProBot

bot = commands.Bot(command_prefix="!", intents=intents)

# ===================== DB Access =====================
bot.db = db
bot.wallets = wallets_collection
bot.pending = pending_collection

# ===================== Slash Commands =====================
from commands.ping import ping
from commands.embed import embed
from commands.trade import trade
from commands.clear import clear
from commands.wallet import wallet
from commands.deposit import deposit

# ===================== Handlers =====================
from admin.wallet_admin import handle_admin_message
from commands.tickets import handle_ticket_message, handle_call_message
from commands.roles_info import handle_roles_message
from commands.roles_price import handle_sale_message
from commands.admin_role_commands import handle_admin_role_message
from commands.role_subscription import check_roles_task

# ===================== Ready =====================
@bot.event
async def on_ready():
    print(f"🟢 Bot Online | {bot.user}")

    try:
        await mongo_client.admin.command("ping")
        print("✅ MongoDB Connected Successfully")
    except Exception as e:
        print("❌ MongoDB Connection Failed:", e)

    try:
        bot.tree.clear_commands(guild=None)
        bot.tree.add_command(ping)
        bot.tree.add_command(embed)
        bot.tree.add_command(trade)
        bot.tree.add_command(clear)
        bot.tree.add_command(wallet)
        bot.tree.add_command(deposit)

        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print("❌ Slash Sync Error:", e)

    try:
        bot.loop.create_task(check_roles_task(bot))
        bot.loop.create_task(clean_expired_deposits())
        print("⏳ Background tasks started")
    except Exception as e:
        print("❌ Task error:", e)


# ===================== ProBot Listener =====================
@bot.event
async def on_message(message: discord.Message):

    # ================= ProBot Monitor =================
    if message.author.id == PROBOT_ID:

        content = message.content

        if "قام بتحويل" in content:

            # استخراج المبلغ
            amount_match = re.search(r"(\d[\d,]*)", content)
            if not amount_match:
                return

            transferred_amount = int(amount_match.group(1).replace(",", ""))

            # التأكد إن التحويل للحساب الصحيح
            if str(PROBOT_RECEIVER_ID) not in content:
                return

            # البحث عن عملية مطابقة
            pending = await bot.pending.find_one({
                "total_required": transferred_amount,
                "status": "waiting_transfer"
            })

            if pending:
                await bot.pending.update_one(
                    {"_id": pending["_id"]},
                    {"$set": {"status": "ready_to_confirm"}}
                )

                user = bot.get_user(pending["user_id"])
                if user:
                    await user.send(
                        f"✅ تم استلام {transferred_amount:,} Credits\n"
                        f"يمكنك الآن الضغط على تأكيد الإضافة."
                    )

    # ================= Other Handlers =================
    if message.author.bot:
        return

    handlers = [
        lambda: handle_call_message(message),
        lambda: handle_ticket_message(message, bot),
        lambda: handle_roles_message(message),
        lambda: handle_sale_message(message),
        lambda: handle_admin_message(bot, message),
        lambda: handle_admin_role_message(bot, message),
    ]

    for handler in handlers:
        try:
            await handler()
        except Exception as e:
            print("❌ Handler error:", e)

    await bot.process_commands(message)


# ===================== تنظيف العمليات المنتهية =====================
async def clean_expired_deposits():
    while True:
        now = datetime.utcnow()

        await bot.pending.delete_many({
            "created_at": {"$lt": now - timedelta(minutes=DEPOSIT_TIMEOUT)},
            "status": "waiting_transfer"
        })

        await asyncio.sleep(60)


# ===================== Error Handler =====================
@bot.event
async def on_command_error(ctx, error):
    print("⚠️ Command Error:", error)


# ===================== Run =====================
bot.run(BOT_TOKEN)
