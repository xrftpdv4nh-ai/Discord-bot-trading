import discord
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime
import math

from config import (
    DEPOSIT_CHANNEL_ID,
    PROBOT_FEE_RATE,
    PROBOT_RECEIVER_ID,
    DEPOSIT_TIMEOUT,
    ADMIN_IDS
)


# ================== VIEW ==================
class DepositView(View):
    def __init__(self, user_id: int, deposit_id):
        super().__init__(timeout=DEPOSIT_TIMEOUT * 60)
        self.user_id = user_id
        self.deposit_id = deposit_id

    # زر إلغاء العملية
    @discord.ui.button(label="❌ إلغاء العملية", style=discord.ButtonStyle.danger)
    async def cancel_deposit(self, interaction: discord.Interaction, button: Button):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ هذا الزر مخصص لصاحب العملية فقط.",
                ephemeral=True
            )
            return

        await interaction.client.pending.delete_one({"_id": self.deposit_id})

        await interaction.response.edit_message(
            content="❌ تم إلغاء عملية الإيداع بنجاح.",
            embed=None,
            view=None
        )


# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد عبر ProBot")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):

    if interaction.channel.id != DEPOSIT_CHANNEL_ID:
        await interaction.response.send_message("🚫 هذا الروم مخصص للشحن فقط.")
        return

    if points <= 0:
        await interaction.response.send_message("❌ عدد النقاط يجب أن يكون أكبر من صفر.")
        return

    total_required = math.ceil(points / (1 - PROBOT_FEE_RATE))

    result = await interaction.client.pending.insert_one({
        "user_id": interaction.user.id,
        "points": points,
        "total_required": total_required,
        "status": "waiting_transfer",
        "channel_id": interaction.channel.id,
        "created_at": datetime.utcnow()
    })

    embed = discord.Embed(
        title="🚀 TRONO PROBOT DEPOSIT",
        color=0x3498db
    )

    embed.add_field(name="👤 المستخدم", value=interaction.user.mention, inline=False)
    embed.add_field(name="💎 النقاط المطلوبة", value=f"```{points:,}```", inline=True)
    embed.add_field(name="💳 المطلوب تحويله", value=f"```{total_required:,} Credits```", inline=False)
    embed.add_field(name="🏦 الحساب المستلم", value=f"<@{PROBOT_RECEIVER_ID}>", inline=False)
    embed.add_field(name="⏳ المهلة", value=f"```{DEPOSIT_TIMEOUT} دقائق```", inline=False)

    embed.set_footer(text="سيتم إضافة النقاط تلقائيًا بعد استلام التحويل")

    view = DepositView(interaction.user.id, result.inserted_id)

    await interaction.response.send_message(embed=embed, view=view)
