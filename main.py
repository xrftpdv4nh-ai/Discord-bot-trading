import discord
from discord.ext import commands

from config import BOT_TOKEN

# Slash Commands
from commands.ping import ping
from commands.embed import embed
from commands.trade import trade
from commands.clear import clear
from commands.wallet import wallet
from commands.deposit import deposit  # ✅ أمر الديبوزت فقط

# Handlers
from commands.deposit import handle_proof_message
from admin.wallet_admin import handle_admin_message


# ===================== Intents =====================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ===================== Ready =====================
@bot.event
async def on_ready():
    print("🟢 Bot Online")

    # ❗ مهم: متعملش clear إلا مرة واحدة
    bot.tree.clear_commands(guild=None)

    # تسجيل الأوامر
    bot.tree.add_command(ping)
    bot.tree.add_command(embed)
    bot.tree.add_command(trade)
    bot.tree.add_command(clear)
    bot.tree.add_command(wallet)
    bot.tree.add_command(deposit)

    await bot.tree.sync()
    print("✅ Commands Synced")


# ===================== Messages =====================
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # 1️⃣ التقاط إثبات التحويل (صور فقط)
    try:
        await handle_proof_message(message)
    except Exception as e:
        print("❌ handle_proof_message error:", e)

    # 2️⃣ أوامر الأدمن النصية
    try:
        await handle_admin_message(bot, message)
    except Exception as e:
        print("❌ handle_admin_message error:", e)

    # 3️⃣ ضروري لتشغيل أي أوامر prefix
    await bot.process_commands(message)


# ===================== Run =====================
bot.run(BOT_TOKEN)
