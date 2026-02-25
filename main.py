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

        # نتأكد إن الرسالة تحويل
        if "قام بتحويل" in content and "لـ" in content:

            # استخراج الرقم بعد $
            amount_match = re.search(r"\$(\d[\d,]*)", content)
            if not amount_match:
                return

            net_received = int(amount_match.group(1).replace(",", ""))

            # استخراج الحساب المستلم
            receiver_match = re.search(r"لـ <@!?(\d+)>", content)
            if not receiver_match:
                return

            receiver_id = int(receiver_match.group(1))

            # لازم يكون التحويل لحسابنا
            if receiver_id != PROBOT_RECEIVER_ID:
                return

            # نجيب كل العمليات المعلقة
            pending_list = await bot.pending.find({
                "status": "waiting_transfer"
            }).to_list(length=20)

            for pending in pending_list:

                expected_points = pending["points"]
                expected_net = round(expected_points * (1 - PROBOT_FEE_RATE))

                channel = bot.get_channel(pending["channel_id"])
                user_id = pending["user_id"]

                # نسمح فرق 1 بسبب التقريب
                if abs(net_received - expected_net) <= 1:

                    # إضافة النقاط
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

                    break
                else:
                    # مبلغ غير مطابق
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
