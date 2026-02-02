import discord
from discord.ext import commands
from discord import app_commands

from config import BOT_TOKEN
from commands.trade import TradeCommand

# ===== INTENTS =====
intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # حتى لو مش مستخدمين roles دلوقتي

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

@bot.event
async def on_ready():
    try:
        print("🟢 Bot connected")

        # امسح أي أوامر قديمة
        bot.tree.clear_commands(guild=None)

        # أضف أمر trade فقط
        trade_cmd = TradeCommand()
        bot.tree.add_command(trade_cmd.trade)

        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")

    except Exception as e:
        print("❌ on_ready error:", e)

# أمر اختبار بسيط جدًا
@bot.tree.command(name="test", description="simple test")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("✅ test works", ephemeral=True)

bot.run(BOT_TOKEN)
