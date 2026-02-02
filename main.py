import discord
from discord.ext import commands
from discord import app_commands

from config import BOT_TOKEN
from commands.trade import TradeCommand
from commands.admin import AdminCommands

intents = discord.Intents.default()
intents.members = True  # مهم عشان Roles

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        trade_cmd = TradeCommand()

        # مسح أي أوامر قديمة (user trade)
        bot.tree.clear_commands(guild=None)

        # أوامر التداول
        bot.tree.add_command(trade_cmd.trade)

        # أوامر الأدمن
        bot.tree.add_command(AdminCommands())

        synced = await bot.tree.sync()
        print(f"✅ Bot is online as {bot.user}")
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Sync error: {e}")


@bot.tree.command(name="ping", description="Test bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong 😂")


if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("❌ BOT_TOKEN not found")
