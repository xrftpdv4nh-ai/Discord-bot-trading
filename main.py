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
from commands.deposit import deposit


# ===================== Ready =====================
@bot.event
async def on_ready():
    print(f"🟢 Bot Online | {bot.user}")
    await mongo_client.admin.command("ping")
    print("✅ MongoDB Connected")

    bot.tree.clear_commands(guild=None)
    bot.tree.add_command(deposit)
    await bot.tree.sync()

    bot.loop.create_task(clean_expired_deposits())


# ===================== ProBot Auto System =====================
@bot.event
async def on_message(message: discord.Message):

    # ===== لو الرسالة من بروبوت =====
    if message.author.id == PROBOT_ID:

        content = message.content

        if "قام بتحويل" in content:

            # استخراج الصافي
            matches = re.findall(r"(\d[\d,]*)\$", content)
            if not matches:
                return

            net_received = int(matches[-1].replace(",", ""))

            # التأكد من الحساب المستلم
            if str(PROBOT_RECEIVER_ID) not in content:
                return

            # استخراج ID الشخص اللي حول
            mention_match = re.search(r"<@!?(\d+)>", content)
            if not mention_match:
                return

            user_id = int(mention_match.group(1))

            pending = await bot.pending.find_one({
                "user_id": user_id,
                "status": "waiting_transfer"
            })

            if not pending:
                return

            expected_points = pending["points"]
            expected_net = round(expected_points * (1 - PROBOT_FEE_RATE))

            channel = bot.get_channel(pending["channel_id"])

            # ================= نجاح =================
            if net_received == expected_net:

                await bot.wallets.update_one(
                    {"user_id": user_id},
                    {
                        "$inc": {
                            "balance": expected_points,
                            "total_deposit": expected_points
                        },
                        "$set": {"last_update": datetime.utcnow()}
                    },
                    upsert=True
                )

                await bot.pending.delete_one({"_id": pending["_id"]})

                if channel:
                    await channel.send(
                        f"✅ <@{user_id}> تم استلام التحويل بنجاح\n"
                        f"💎 تم إضافة {expected_points:,} نقطة إلى رصيدك."
                    )

            # ================= خطأ مبلغ =================
            else:
                if channel:
                    await channel.send(
                        f"❌ <@{user_id}> تم تحويل مبلغ غير مطابق.\n"
                        f"المطلوب صافي: {expected_net:,}\n"
                        f"الواصل: {net_received:,}"
                    )

    if message.author.bot:
        return

    await bot.process_commands(message)


# ===================== تنظيف المهلة =====================
async def clean_expired_deposits():
    while True:
        now = datetime.utcnow()

        expired = await bot.pending.find({
            "created_at": {"$lt": now - timedelta(minutes=DEPOSIT_TIMEOUT)},
            "status": "waiting_transfer"
        }).to_list(length=50)

        for item in expired:
            channel = bot.get_channel(item["channel_id"])
            if channel:
                await channel.send(
                    f"❌ <@{item['user_id']}> انتهت مهلة التحويل."
                )

        await bot.pending.delete_many({
            "created_at": {"$lt": now - timedelta(minutes=DEPOSIT_TIMEOUT)},
            "status": "waiting_transfer"
        })

        await asyncio.sleep(60)


bot.run(BOT_TOKEN)
