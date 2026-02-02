import discord
from discord.ext import commands

from config import BOT_TOKEN

# Slash Commands
from commands.ping import ping
from commands.embed import embed
from commands.trade import trade
from commands.clear import clear
from commands.wallet import wallet
from commands.deposit import deposit

# Admin text commands (no prefix)
from admin.wallet_admin import handle_admin_message

intents = discord.Intents.default()
intents.message_content = True  # مهم جدًا علشان قراءة الرسائل

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("🟢 Bot Online")

    bot.tree.clear_commands(guild=None)

    bot.tree.add_command(ping)
    bot.tree.add_command(embed)
    bot.tree.add_command(trade)
    bot.tree.add_command(clear)
    bot.tree.add_command(wallet)
    bot.tree.add_command(deposit)
    
    await bot.tree.sync()
    print("✅ Commands Synced")

@bot.event
async def on_message(message):
    # أوامر الأدمن النصية (add / remove / ahelp / جاهز)
    handle_admin_message(bot, message)

    # خلي أي أوامر تانية شغالة (لو عندك prefix أو غيره)
    await bot.process_commands(message)

bot.run(BOT_TOKEN)
