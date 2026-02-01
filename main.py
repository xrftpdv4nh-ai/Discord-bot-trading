import discord
from discord.ext import commands
from discord import app_commands

from config import BOT_TOKEN

# Intents
intents = discord.Intents.default()

# Bot instance
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# -------- EVENTS -------- #

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Bot is online as {bot.user}")
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# -------- TEST COMMAND -------- #

@bot.tree.command(name="ping", description="Test bot response")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! Bot is working.")

# -------- RUN BOT -------- #

if BOT_TOKEN is None:
    print("❌ BOT_TOKEN not found. Check Railway Variables.")
else:
    bot.run(BOT_TOKEN)
