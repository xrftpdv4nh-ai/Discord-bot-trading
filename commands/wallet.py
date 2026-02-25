import discord
from discord import app_commands

@app_commands.command(name="wallet", description="عرض محفظة أي عضو")
@app_commands.describe(member="اختر عضو لعرض محفظته")
async def wallet(interaction: discord.Interaction, member: discord.Member = None):

    target = member if member else interaction.user

    data = await interaction.client.wallets.find_one({
        "user_id": target.id
    })

    if not data:
        data = {
            "balance": 0,
            "total_deposit": 0,
            "total_profit": 0,
            "total_loss": 0,
            "wins": 0,
            "losses": 0,
            "games_played": 0
        }

    embed = discord.Embed(
        title="💼 TRONO WALLET",
        color=0x2ecc71
    )

    embed.set_thumbnail(url=target.display_avatar.url)

    embed.add_field(
        name="👤 المستخدم",
        value=target.mention,
        inline=False
    )

    embed.add_field(
        name="💰 الرصيد",
        value=f"```{data.get('balance', 0):,}```",
        inline=True
    )

    embed.add_field(
        name="📥 إجمالي الإيداع",
        value=f"```{data.get('total_deposit', 0):,}```",
        inline=True
    )

    embed.add_field(
        name="📈 الأرباح",
        value=f"```{data.get('total_profit', 0):,}```",
        inline=True
    )

    embed.add_field(
        name="📉 الخسائر",
        value=f"```{data.get('total_loss', 0):,}```",
        inline=True
    )

    embed.add_field(
        name="🎮 عدد اللعبات",
        value=f"```{data.get('games_played', 0):,}```",
        inline=True
    )

    embed.add_field(
        name="🏆 الفوز / ❌ الخسارة",
        value=f"```{data.get('wins',0)} / {data.get('losses',0)}```",
        inline=True
    )

    embed.set_footer(text="Trono Trading System")

    await interaction.response.send_message(embed=embed)
