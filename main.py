import discord
from discord.ext import commands
from discord import app_commands

from config import BOT_TOKEN
from commands.user import UserCommands
from commands.admin import AdminCommands

# -------- INTENTS -------- #
intents = discord.Intents.default()

# -------- BOT INSTANCE -------- #
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# -------- EVENTS -------- #
@bot.event
async def on_ready():
    try:
        # إضافة أوامر المستخدم
        bot.tree.add_command(UserCommands())

        # إضافة أوامر الأدمن
        bot.tree.add_command(AdminCommands())

        synced = await bot.tree.sync()
        print(f"✅ Bot is online as {bot.user}")
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# -------- TEST COMMAND -------- #
@bot.tree.command(name="ping", description="Test bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong 😂")

# -------- RUN BOT -------- #
if BOT_TOKEN is None:
    print("❌ BOT_TOKEN not found. Check Railway Variables.")
else:
    bot.run(BOT_TOKEN)
