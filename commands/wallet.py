import discord
from discord import app_commands
from datetime import datetime, date

# ====== ROLE IDS ======
PRO_ROLE_ID = 1467922966485668118
VIP_ROLE_ID = 1467923207389712556

# ====== GET LEVEL ======
def get_user_level(member: discord.Member):
    roles = [r.id for r in member.roles]

    if VIP_ROLE_ID in roles:
        return {"name": "VIP", "daily_limit": 35}
    elif PRO_ROLE_ID in roles:
        return {"name": "PRO", "daily_limit": 20}
    else:
        return {"name": "USER", "daily_limit": 12}


@app_commands.command(name="wallet", description="عرض محفظتك")
async def wallet(interaction: discord.Interaction):

    wallets = interaction.client.wallets
    uid = interaction.user.id

    # ====== GET WALLET FROM MONGO ======
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

    # ====== DAILY TRADES ======
    from commands.trade import user_data  # مهم

    today = str(date.today())

    if uid in user_data and user_data[uid]["date"] == today:
        trades_today = user_data[uid]["trades_today"]
    else:
        trades_today = 0

    level = get_user_level(interaction.user)
    remaining = max(0, level["daily_limit"] - trades_today)

    # ====== DYNAMIC COLOR ======
    if balance > 500000:
        color = 0xf1c40f  # ذهبي
    elif balance > 100000:
        color = 0x2ecc71  # أخضر
    else:
        color = 0x3498db  # أزرق

    net = total_profit - total_loss

    # ====== EMBED ======
    embed = discord.Embed(
        title="💎 TRONO WALLET",
        description="━━━━━━━━━━━━━━━━━━",
        color=color
    )

    # صورة الحساب فوق يمين
    embed.set_thumbnail(url=interaction.user.display_avatar.url)

    # الصف الأول
    embed.add_field(
        name="💰 الرصيد الحالي",
        value=f"```{balance:,}```",
        inline=True
    )

    embed.add_field(
        name="📥 إجمالي الإيداع",
        value=f"```{total_deposit:,}```",
        inline=True
    )

    # الصف الثاني
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

    # الصف الثالث
    embed.add_field(
        name="📊 صافي الأداء",
        value=f"```{net:,}```",
        inline=True
    )

    embed.add_field(
        name="👑 المستوى",
        value=f"```{level['name']}```",
        inline=True
    )

    # سطر لوحده
    embed.add_field(
        name="📅 الصفقات المتبقية اليوم",
        value=f"```{remaining} / {level['daily_limit']}```",
        inline=False
    )

    embed.set_footer(text="Trono Trading System • Live Data")

    await interaction.response.send_message(embed=embed)
