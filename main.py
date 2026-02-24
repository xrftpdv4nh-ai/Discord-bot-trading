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

    try:
        await mongo_client.admin.command("ping")
        print("✅ MongoDB Connected")
    except Exception as e:
        print("❌ Mongo Error:", e)

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
        print("❌ Sync Error:", e)

    bot.loop.create_task(clean_expired_deposits())


# ===================== ProBot Listener =====================
@bot.event
async def on_message(message: discord.Message):

    # ===== مراقبة بروبوت =====
    if message.author.id == PROBOT_ID:

        content = message.content

        if "قام بتحويل" in content:

            # استخراج الرقم اللي قبل $
            matches = re.findall(r"(\d[\d,]*)\$", content)
            if not matches:
                return

            net_received = int(matches[-1].replace(",", ""))

            # التأكد إن التحويل للحساب الصحيح
            if str(PROBOT_RECEIVER_ID) not in content:
                return

            # نجيب كل العمليات المنتظرة
            pending_list = await bot.pending.find({
                "status": "waiting_transfer"
            }).to_list(length=20)

            for pending in pending_list:

                # نحسب المبلغ اللي المستخدم المفروض يكون حوله
                expected_total = pending["total_required"]

                # نحسب الصافي المتوقع من total_required
                expected_net = int(expected_total * 0.95)

                # لو الصافي مطابق
                if net_received == expected_net:

                    await bot.pending.update_one(
                        {"_id": pending["_id"]},
                        {"$set": {"status": "ready_to_confirm"}}
                    )

                    user = bot.get_user(pending["user_id"])
                    if user:
                        await user.send(
                            f"✅ تم استلام {net_received:,} Credits\n"
                            f"يمكنك الآن الضغط على تأكيد الإضافة."
                        )

                    break

    # ===== بقية النظام =====
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
