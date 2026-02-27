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
tickets_collection = db.tickets  # 👈 جديد للتكت

# ===================== Intents =====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot.wallets = wallets_collection
bot.pending = pending_collection
bot.tickets = tickets_collection  # 👈 ربط التكت
bot.db = db
# ===================== Slash Commands =====================
from commands.deposit import deposit
from commands.wallet import wallet
from commands.trade import trade
from commands.clear import clear
from commands.embed import embed
from commands.ping import ping
from commands.admin_pending import admin_pending

import commands.ticket_system as ticket_system
from commands.ticket_system import TicketView, TicketControlView

from commands.emoji_manager import handle_emoji_message

# ===================== Message Commands =====================
from commands.roles_info import handle_roles_message
from commands.roles_price import handle_sale_message
from commands.admin_role_commands import handle_admin_role_message
from admin.wallet_admin import handle_admin_message
from commands.ticket_system import handle_support_call
from commands.ticket_system import handle_notify_user
from admin.trade_control import handle_trade_control

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
        bot.tree.add_command(admin_pending)
        bot.tree.add_command(ticket_system.ticket_panel)

        await bot.tree.sync()
        print("✅ Slash Commands Synced")

    except Exception as e:
        print("❌ Sync Error:", e)

    # 👇 Persistent Views (تشتغل بعد الريستارت)
    bot.add_view(TicketView())
    bot.add_view(TicketControlView())

    bot.loop.create_task(clean_expired_deposits())


# ===================== on_message =====================
@bot.event
async def on_message(message: discord.Message):

    if message.author.bot and message.author.id != PROBOT_ID:
        return

    # ===== ProBot Detection =====
    if message.author.id == PROBOT_ID:

        content = message.content

        if "قام بتحويل" in content and "لـ" in content:

            amount_match = re.search(r"\$(\d[\d,]*)", content)
            if amount_match:

                net_received = int(amount_match.group(1).replace(",", ""))

                receiver_match = re.search(r"لـ <@!?(\d+)>", content)
                if receiver_match:

                    receiver_id = int(receiver_match.group(1))

                    if receiver_id == PROBOT_RECEIVER_ID:

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

    # ===== أوامر بدون برفكس =====
    if not message.author.bot:
        await handle_roles_message(message)
        await handle_sale_message(message)
        await handle_admin_role_message(bot, message)
        await handle_admin_message(bot, message)
        await handle_emoji_message(bot, message)
        await handle_support_call(bot, message)
        await handle_notify_user(bot, message)
        await handle_trade_control(bot, message)
        
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


# ===================== Run =====================
bot.run(BOT_TOKEN)
