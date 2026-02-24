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
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

bot.wallets = wallets_collection
bot.pending = pending_collection

# ===================== Slash Commands =====================
from commands.ping import ping
from commands.embed import embed
from commands.trade import trade
from commands.clear import clear
from commands.wallet import wallet
from commands.deposit import deposit

# ===================== Ready =====================
@bot.event
async def on_ready():
    print(f"🟢 Bot Online | {bot.user}")
    await mongo_client.admin.command("ping")
    await bot.tree.sync()
    bot.loop.create_task(clean_expired_deposits())


# ===================== ProBot Listener =====================
@bot.event
async def on_message(message: discord.Message):

    # ================= ProBot Monitor =================
    if message.author.id == PROBOT_ID:

        content = message.content

        if "قام بتحويل" in content:

            # استخراج المبلغ اللي وصل فعليًا
            amount_match = re.search(r"(\d[\d,]*)\$", content)
            if not amount_match:
                return

            net_received = int(amount_match.group(1).replace(",", ""))

            # التأكد إن التحويل للحساب الصحيح
            if str(PROBOT_RECEIVER_ID) not in content:
                return

            # البحث عن عملية waiting
            pending = await bot.pending.find_one({
                "status": "waiting_transfer"
            })

            if not pending:
                return

            expected_points = pending["points"]

            # 👑 نقارن الصافي اللي وصل بالنقاط المطلوبة
            if abs(net_received - expected_points) <= 1:

                await bot.pending.update_one(
                    {"_id": pending["_id"]},
                    {"$set": {"status": "ready_to_confirm"}}
                )

                user = bot.get_user(pending["user_id"])
                if user:
                    await user.send(
                        f"✅ تم استلام {net_received:,} Credits صافي\n"
                        f"يمكنك الآن الضغط على تأكيد الإضافة."
                    )

    # ================= Continue normal handlers =================
    if message.author.bot:
        return

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


# ===================== Run =====================
bot.run(BOT_TOKEN)
