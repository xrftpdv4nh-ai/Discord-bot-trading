import discord
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime
import uuid

from config import DEPOSIT_CHANNEL_ID

# ================== AUTO VIEW ==================
class ProBotAutoView(View):
    def __init__(self, points, req_id):
        super().__init__(timeout=60)
        self.points = points
        self.req_id = req_id

    @discord.ui.button(label="⚡ تأكيد التحويل عبر ProBot", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)

        wallets = interaction.client.wallets

        # 💎 إضافة الرصيد فوراً
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
            name="⚡ الحالة",
            value="```تم الإضافة بنجاح```",
            inline=True
        )

        embed.add_field(
            name="📅 التوقيت",
            value=f"```{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}```",
            inline=False
        )

        embed.set_footer(text=f"Transaction ID • {self.req_id}")

        for c in self.children:
            c.disabled = True

        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            embed=embed,
            view=self
        )


# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد عبر ProBot")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):

    await interaction.response.defer(ephemeral=True)

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

    req_id = uuid.uuid4().hex[:8]

    embed = discord.Embed(
        title="🚀 TRONO PROBOT DEPOSIT",
        description="━━━━━━━━━━━━━━━━━━",
        color=0x3498db
    )

    embed.add_field(
        name="💎 النقاط المطلوبة",
        value=f"```{points:,}```",
        inline=True
    )

    embed.add_field(
        name="💵 القيمة التقديرية",
        value=f"```{points/100:,.2f} EGP```",
        inline=True
    )

    embed.add_field(
        name="⚡ طريقة الشحن",
        value="```ProBot Auto Transfer```",
        inline=False
    )

    embed.set_footer(text=f"Transaction ID • {req_id}")

    await interaction.followup.send(
        embed=embed,
        view=ProBotAutoView(points, req_id),
        ephemeral=True
    )
