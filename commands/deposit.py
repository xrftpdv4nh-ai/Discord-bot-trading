import discord
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime

from config import DEPOSIT_CHANNEL_ID


# ================== AUTO VIEW ==================
class ProBotAutoView(View):
    def __init__(self, points: int):
        super().__init__(timeout=60)
        self.points = points

    @discord.ui.button(label="⚡ تأكيد الإضافة", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):

        await interaction.response.defer(ephemeral=True)

        try:
            wallets = interaction.client.wallets

            await wallets.update_one(
                {"user_id": interaction.user.id},
                {
                    "$inc": {
                        "balance": self.points,
                        "total_deposit": self.points
                    },
                    "$set": {
                        "last_update": datetime.utcnow()
                    }
                },
                upsert=True
            )

            embed = discord.Embed(
                title="💎 TRONO AUTO DEPOSIT",
                description="━━━━━━━━━━━━━━━━━━",
                color=0x2ecc71
            )

            embed.add_field(
                name="💰 النقاط المضافة",
                value=f"```{self.points:,}```",
                inline=True
            )

            embed.add_field(
                name="📅 التوقيت",
                value=f"```{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}```",
                inline=True
            )

            embed.add_field(
                name="⚡ الحالة",
                value="```تمت الإضافة بنجاح```",
                inline=False
            )

            embed.set_footer(text="Trono Trading System • Live")

            for item in self.children:
                item.disabled = True

            await interaction.followup.edit_message(
                message_id=interaction.message.id,
                embed=embed,
                view=self
            )

        except Exception as e:
            print("Deposit Confirm Error:", e)
            await interaction.followup.send(
                "❌ حدث خطأ أثناء الإضافة",
                ephemeral=True
            )


# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد عبر ProBot")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):

    # 🔥 نرد فوراً علشان نمنع Timeout
    await interaction.response.defer(ephemeral=True)

    try:
        if interaction.channel.id != DEPOSIT_CHANNEL_ID:
            await interaction.followup.send(
                "🚫 هذا الروم مخصص للشحن فقط",
                ephemeral=True
            )
            return

        if points <= 0:
            await interaction.followup.send(
                "❌ عدد النقاط يجب أن يكون أكبر من صفر",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🚀 TRONO PROBOT DEPOSIT",
            description="━━━━━━━━━━━━━━━━━━",
            color=0x3498db
        )

        embed.add_field(
            name="💎 النقاط",
            value=f"```{points:,}```",
            inline=True
        )

        embed.add_field(
            name="💵 القيمة التقريبية",
            value=f"```{points/100:,.2f} EGP```",
            inline=True
        )

        embed.add_field(
            name="⚡ النظام",
            value="```إضافة فورية تلقائية```",
            inline=False
        )

        embed.set_footer(text="اضغط على الزر لتأكيد الشحن")

        await interaction.followup.send(
            embed=embed,
            view=ProBotAutoView(points),
            ephemeral=True
        )

    except Exception as e:
        print("Deposit Command Error:", e)
        await interaction.followup.send(
            "❌ حدث خطأ غير متوقع",
            ephemeral=True
        )
