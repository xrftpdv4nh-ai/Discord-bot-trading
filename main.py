import discord
from discord.ext import commands
from discord import app_commands

from config import BOT_TOKEN
from commands.trade import TradeCommand
from commands.admin import AdminCommands

# ===== INTENTS =====
intents = discord.Intents.default()
intents.members = True  # مهم جدًا عشان Roles (Pro / VIP)

# ===== BOT =====
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ===== EVENTS =====
@bot.event
async def on_ready():
    try:
        # إنشاء كائن أوامر التداول
        trade_cmd = TradeCommand()

        # مسح أي أوامر قديمة (user trade)
        bot.tree.clear_commands(guild=None)

        # إضافة أوامر التداول
        bot.tree.add_command(trade_cmd.trade)

        # إضافة أوامر الأدمن
        bot.tree.add_command(AdminCommands())

        # مزامنة الأوامر
        synced = await bot.tree.sync()

        print("=================================")
        print(f"✅ Bot is online as {bot.user}")
        print(f"✅ Synced {len(synced)} command(s)")
        print("=================================")

    except Exception as e:
        print(f"❌ Sync error: {e}")

# ===== TEST COMMAND =====
@bot.tree.command(name="ping", description="Test bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong 😂")

# ===== RUN =====
if not BOT_TOKEN:
    print("❌ BOT_TOKEN not found. Check Railway Variables.")
else:
    bot.run(BOT_TOKEN)
