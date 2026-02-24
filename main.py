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

    try:
        await mongo_client.admin.command("ping")
        print("✅ MongoDB Connected")
    except Exception as e:
        print("❌ Mongo Error:", e)

    try:
        bot.tree.clear_commands(guild=None)
        bot.tree.add_command(deposit)
        await bot.tree.sync()
        print("✅ Slash Commands Synced")
    except Exception as e:
        print("❌ Sync Error:", e)

    bot.loop.create_task(clean_expired_deposits())


# ===================== ProBot Auto Detection =====================
@bot.event
async def on_message(message: discord.Message):

    # ===== لو الرسالة من ProBot =====
    if message.author.id == PROBOT_ID:

        content = message.content

        if "قام بتحويل" in content:

            # ================= استخراج كل الأرقام =================
            numbers = re.findall(r"\d[\d,]*", content)
            if not numbers:
                return

            net_received = max(int(num.replace(",", "")) for num in numbers)

            # ================= استخراج الحساب المستلم =================
            receiver_match = re.search(r"<@!?(\d+)>", content)
            if not receiver_match:
                return

            receiver_id = int(receiver_match.group(1))

            if receiver_id != PROBOT_RECEIVER_ID:
                return

            # ================= استخراج الشخص اللي حول =================
            sender_match = re.search(r"قام بتحويل.*?(\d+)", content)
            mention_match = re.search(r"<@!?(\d+)>", content)

            # نجيب أول منشن في الرسالة (المحول)
            mentions = re.findall(r"<@!?(\d+)>", content)
            if not mentions:
                return

            user_id = int(mentions[0])

            # ================= البحث عن عملية =================
            pending = await bot.pending.find_one({
                "user_id": user_id,
                "status": "waiting_transfer"
            })

            if not pending:
                return

            expected_net = pending.get("expected_net")
            expected_points = pending.get("points")
            channel = bot.get_channel(pending.get("channel_id"))

            if not expected_net or not expected_points:
                return

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
                        f"✅ <@{user_id}> تم استلام {net_received:,} Credits بنجاح\n"
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


# ===================== تنظيف العمليات المنتهية =====================
async def clean_expired_deposits():
    while True:
        now = datetime.utcnow()

        expired = await bot.pending.find({
            "created_at": {"$lt": now - timedelta(minutes=DEPOSIT_TIMEOUT)},
            "status": "waiting_transfer"
        }).to_list(length=50)

        for item in expired:
            channel = bot.get_channel(item.get("channel_id"))
            if channel:
                await channel.send(
                    f"❌ <@{item['user_id']}> انتهت مهلة التحويل."
                )

        await bot.pending.delete_many({
            "created_at": {"$lt": now - timedelta(minutes=DEPOSIT_TIMEOUT)},
            "status": "waiting_transfer"
        })

        await asyncio.sleep(60)


# ===================== Run =====================
bot.run(BOT_TOKEN)
