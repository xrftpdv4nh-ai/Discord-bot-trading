import discord
from discord.ext import commands

from config import BOT_TOKEN
from commands.ping import ping
from commands.embed import embed
from commands.trade import trade
from commands.clear import clear
from commands.wallet import wallet
from admin.wallet_admin import WalletAdmin

intents = discord.Intents.default()
intents.message_content = True  # مهم لأوامر !
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
    bot.add_cog(WalletAdmin(bot))
    # ✅ هنا التصحيح
    bot.add_cog(AdminWallet(bot))

    await bot.tree.sync()
    print("✅ Commands Synced")

bot.run(BOT_TOKEN)
