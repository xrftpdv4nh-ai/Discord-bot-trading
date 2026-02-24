import discord
from discord import app_commands
from datetime import datetime


@app_commands.command(name="wallet", description="عرض محفظتك")
async def wallet(interaction: discord.Interaction):

    wallets = interaction.client.wallets
    uid = interaction.user.id

    data = await wallets.find_one({"user_id": uid})

    if not data:
        data = {
            "user_id": uid,
            "balance": 0,
            "total_deposit": 0,
            "total_profit": 0,
            "total_loss": 0,
            "last_update": str(datetime.now())
        }
        await wallets.insert_one(data)

    balance = data.get("balance", 0)
    total_deposit = data.get("total_deposit", 0)
    total_profit = data.get("total_profit", 0)
    total_loss = data.get("total_loss", 0)

    # 🎨 لون ديناميكي
    if balance > 500000:
        color = 0xf1c40f  # ذهبي
    elif balance > 100000:
        color = 0x2ecc71  # أخضر
    else:
        color = 0x3498db  # أزرق

    embed = discord.Embed(
        title="💎  TRONO WALLET",
        description="━━━━━━━━━━━━━━━━━━",
        color=color
    )

    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    embed.add_field(
        name="💰 الرصيد الحالي",
        value=f"```{balance:,}```",
        inline=False
    )

    embed.add_field(
        name="📥 إجمالي الإيداع",
        value=f"```{total_deposit:,}```",
        inline=True
    )

    embed.add_field(
        name="📈 إجمالي الأرباح",
        value=f"```{total_profit:,}```",
        inline=True
    )

    embed.add_field(
        name="📉 إجمالي الخسائر",
        value=f"```{total_loss:,}```",
        inline=True
    )

    embed.add_field(
        name="📊 صافي الأداء",
        value=f"```{(total_profit - total_loss):,}```",
        inline=False
    )

    embed.set_footer(
        text="🔐 بياناتك خاصة بك فقط • Trono Trading System"
    )

    await interaction.response.send_message(embed=embed)
