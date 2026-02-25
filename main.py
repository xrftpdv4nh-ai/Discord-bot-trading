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
from commands.wallet import wallet
from commands.trade import trade
from commands.clear import clear
from commands.embed import embed
from commands.ping import ping
from commands.admin_pending import admin_pending

# ===================== Message Handlers =====================
from commands.roles_info import handle_roles_message
from commands.roles_price import handle_sale_message
from commands.admin_role_commands import handle_admin_role_message
from admin.wallet_admin import handle_admin_message

# ===================== Ready =====================
@bot.event
async def on_ready():
    print(f"🟢 Bot Online | {bot.user}")

    await mongo_client.admin.command("ping")
    print("✅ MongoDB Connected")

    # تسجيل الأوامر يدوي (مهم)
    bot.tree.add_command(ping)
    bot.tree.add_command(embed)
    bot.tree.add_command(trade)
    bot.tree.add_command(clear)
    bot.tree.add_command(wallet)
    bot.tree.add_command(deposit)
    bot.tree.add_command(admin_pending)

    synced = await bot.tree.sync()
    print(f"✅ Synced {len(synced)} Slash Commands")

    bot.loop.create_task(clean_expired_deposits())


# ===================== on_message =====================
@bot.event
async def on_message(message: discord.Message):

    # ===== ProBot Detection =====
    if message.author.id == PROBOT_ID:

        content = message.content

        if "قام بتحويل" in content and "لـ" in content:

            amount_match = re.search(r"\$(\d[\d,]*)", content)
            if not amount_match:
                return

            net_received = int(amount_match.group(1).replace(",", ""))

            receiver_match = re.search(r"لـ <@!?(\d+)>", content)
            if not receiver_match:
                return

            receiver_id = int(receiver_match.group(1))

            if receiver_id != PROBOT_RECEIVER_ID:
                return

            pending_list = await bot.pending.find({
                "status": "waiting_transfer"
            }).to_list(length=20)

            for pending in pending_list:

                expected_points = pending["points"]
                user_id = pending["user_id"]
                channel = bot.get_channel(pending["channel_id"])

                if abs(net_received - expected_points) <= 1:

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
                            f"✅ <@{user_id}> تم استلام {net_received:,} Credits\n"
                            f"💎 تم إضافة {expected_points:,} نقطة."
                        )

                    break

    if message.author.bot:
        return

# ===== أوامر بدون برفكس =====
await handle_roles_message(message)
await handle_sale_message(message)
await handle_admin_role_message(bot, message)
await handle_admin_message(bot, message)

await bot.process_commands(message)


# ===================== تنظيف العمليات =====================
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
