import discord
from discord.ext import commands

from config import BOT_TOKEN

# Slash Commands
from commands.ping import ping
from commands.embed import embed
from commands.trade import trade
from commands.clear import clear
from commands.wallet import wallet
from commands.deposit import deposit, DepositView  # ⬅️ مهم

# Handlers
from commands.deposit import handle_proof_message
from admin.wallet_admin import handle_admin_message

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("🟢 Bot Online")

    # 🔴 تسجيل الـ View علشان أزرار Confirm / Reject تشتغل
    # لازم timeout=None جوه DepositView
    bot.add_view(DepositView(None))

    bot.tree.clear_commands(guild=None)

    bot.tree.add_command(ping)
    bot.tree.add_command(embed)
    bot.tree.add_command(trade)
    bot.tree.add_command(clear)
    bot.tree.add_command(wallet)
    bot.tree.add_command(deposit)

    await bot.tree.sync()
    print("✅ Commands Synced")

    # Test admin channel
    try:
        ch = await bot.fetch_channel(1293008901142351952)
        await ch.send("✅ TEST MESSAGE FROM BOT")
        print("✅ Admin channel test sent")
    except Exception as e:
        print("❌ Admin channel test failed:", e)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1️⃣ التقاط إثباتات التحويل
    await handle_proof_message(message)

    # 2️⃣ أوامر الأدمن النصية
    await handle_admin_message(bot, message)

    # 3️⃣ مهم جدًا لتشغيل أي أوامر أخرى
    await bot.process_commands(message)

bot.run(BOT_TOKEN)
