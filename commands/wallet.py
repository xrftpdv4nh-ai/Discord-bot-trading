import discord
from discord import app_commands
from datetime import datetime


@app_commands.command(name="wallet", description="عرض محفظتك")
async def wallet(interaction: discord.Interaction):

    wallets = interaction.client.wallets

    # 🔎 نجيب بيانات المستخدم من Mongo
    data = await wallets.find_one({"user_id": interaction.user.id})

    # 🟢 لو المستخدم مش موجود
    if not data:
        data = {
            "balance": 0,
            "total_deposit": 0,
            "total_profit": 0,
            "total_loss": 0,
            "last_update": str(datetime.now())
        }

        await wallets.insert_one({
            "user_id": interaction.user.id,
            **data
        })

    embed = discord.Embed(
        title="💼 محفظتك",
        color=0x2ecc71
    )

    embed.add_field(
        name="💰 الرصيد الحالي",
        value=f"`{data.get('balance', 0)}`",
        inline=False
    )

    embed.add_field(
        name="📥 إجمالي الإيداع",
        value=f"`{data.get('total_deposit', 0)}`",
        inline=False
    )

    embed.add_field(
        name="📈 إجمالي الأرباح",
        value=f"`{data.get('total_profit', 0)}`",
        inline=False
    )

    embed.add_field(
        name="📉 إجمالي الخسائر",
        value=f"`{data.get('total_loss', 0)}`",
        inline=False
    )

    embed.set_footer(text="🔐 هذه البيانات خاصة بك فقط")

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )
