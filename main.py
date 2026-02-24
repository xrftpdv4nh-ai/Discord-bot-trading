import discord
from discord.ext import commands
import motor.motor_asyncio
import asyncio

from config import BOT_TOKEN, MONGO_URL

# ===================== MongoDB =====================
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = mongo_client.trono_trade
wallets_collection = db.wallets

# ===================== Intents =====================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# نخلي الداتابيز متاحة لكل الملفات
bot.db = db
bot.wallets = wallets_collection

# ===================== Slash Commands =====================
from commands.ping import ping
from commands.embed import embed
from commands.trade import trade
from commands.clear import clear
from commands.wallet import wallet
from commands.deposit import deposit

# ===================== Handlers =====================
from commands.deposit import handle_proof_message
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
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print("❌ Sync Error:", e)

    # تشغيل فحص انتهاء الرولات
    try:
        bot.loop.create_task(check_roles_task(bot))
        print("⏳ Role subscription task started")
    except Exception as e:
        print("❌ Role task error:", e)

# ===================== Global Error Handler =====================
@bot.event
async def on_command_error(ctx, error):
    print("⚠️ Command Error:", error)

# ===================== Messages =====================
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    handlers = [
        lambda: handle_call_message(message),
        lambda: handle_ticket_message(message, bot),
        lambda: handle_roles_message(message),
        lambda: handle_sale_message(message),
        lambda: handle_proof_message(message),
        lambda: handle_admin_message(bot, message),
        lambda: handle_admin_role_message(bot, message),
    ]

    for handler in handlers:
        try:
            await handler()
        except Exception as e:
            print("❌ Handler error:", e)

    await bot.process_commands(message)

# ===================== Run =====================
bot.run(BOT_TOKEN)
