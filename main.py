import discord
from discord.ext import commands

from config import BOT_TOKEN
from commands.ping import ping
from commands.embed import embed

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print("🟢 Bot Online")

    bot.tree.clear_commands(guild=None)

    bot.tree.add_command(ping)
    bot.tree.add_command(embed)

    await bot.tree.sync()

    print("✅ Commands Synced")


bot.run(BOT_TOKEN)
