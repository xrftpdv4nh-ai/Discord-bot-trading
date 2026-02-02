import discord
from discord import app_commands
import json
import os
from datetime import datetime

DATA_FILE = "data/wallets.json"

def load_wallets():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_wallets(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_wallet(user_id: int):
    wallets = load_wallets()
    uid = str(user_id)

    if uid not in wallets:
        wallets[uid] = {
            "balance": 0,
            "total_deposit": 0,
            "total_profit": 0,
            "total_loss": 0,
            "last_update": str(datetime.now())
        }
        save_wallets(wallets)

    return wallets, wallets[uid]

@app_commands.command(name="wallet", description="عرض محفظتك")
async def wallet(interaction: discord.Interaction):
    wallets, data = get_wallet(interaction.user.id)

    embed = discord.Embed(
        title="💼 **محفظتك**",
        color=0x2ecc71
    )

    embed.add_field(
        name="💰 **الرصيد الحالي**",
        value=f"`{data['balance']}`",
        inline=False
    )

    embed.add_field(
        name="📈 **إجمالي الأرباح**",
        value=f"`{data['total_profit']}`",
        inline=False
    )

    embed.set_footer(text="🔐 هذه البيانات خاصة بك فقط")

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )
