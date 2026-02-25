import discord
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime
from config import ADMIN_IDS


# ===================== تحقق الأدمن =====================
def is_authorized(interaction: discord.Interaction) -> bool:
    return (
        interaction.user.id in ADMIN_IDS
        or interaction.user.guild_permissions.administrator
        or interaction.user.id == interaction.guild.owner_id
    )


# ===================== View الأزرار =====================
class PendingActionView(View):
    def __init__(self, deposit_data):
        super().__init__(timeout=None)
        self.deposit_data = deposit_data

    # زر إكمال
    @discord.ui.button(label="✅ إكمال المعاملة", style=discord.ButtonStyle.success)
    async def complete(self, interaction: discord.Interaction, button: Button):

        if not is_authorized(interaction):
            await interaction.response.send_message(
                "❌ هذا الزر مخصص للأدمن فقط.",
                ephemeral=True
            )
            return

        user_id = self.deposit_data["user_id"]
        points = self.deposit_data["points"]

        # إضافة النقاط
        await interaction.client.wallets.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    "balance": points,
                    "total_deposit": points
                },
                "$set": {"last_update": datetime.utcnow()}
            },
            upsert=True
        )

        # حذف العملية
        await interaction.client.pending.delete_one({
            "_id": self.deposit_data["_id"]
        })

        await interaction.response.edit_message(
            content=f"✅ تم إكمال المعاملة وإضافة {points} نقطة لـ <@{user_id}>",
            embed=None,
            view=None
        )

    # زر رفض
    @discord.ui.button(label="❌ رفض المعاملة", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):

        if not is_authorized(interaction):
            await interaction.response.send_message(
                "❌ هذا الزر مخصص للأدمن فقط.",
                ephemeral=True
            )
            return

        await interaction.client.pending.delete_one({
            "_id": self.deposit_data["_id"]
        })

        await interaction.response.edit_message(
            content="❌ تم رفض المعاملة وحذفها.",
            embed=None,
            view=None
        )


# ===================== أمر عرض العمليات =====================
@app_commands.command(name="pending", description="لوحة إدارة العمليات المعلقة")
async def admin_pending(interaction: discord.Interaction):

    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ هذا الأمر مخصص للأدمن فقط.",
            ephemeral=True
        )
        return

    pending_list = await interaction.client.pending.find({
        "status": "waiting_transfer"
    }).to_list(length=20)

    if not pending_list:
        await interaction.response.send_message("✅ لا توجد عمليات معلقة.")
        return

    await interaction.response.send_message("📦 قائمة العمليات المعلقة:")

    for item in pending_list:

        embed = discord.Embed(
            title="💳 عملية إيداع معلقة",
            color=0xf1c40f
        )

        embed.add_field(name="🆔 ID", value=f"```{item['_id']}```", inline=False)
        embed.add_field(name="👤 المستخدم", value=f"<@{item['user_id']}>", inline=False)
        embed.add_field(name="💎 النقاط", value=f"{item['points']}", inline=True)
        embed.add_field(name="💳 المطلوب تحويله", value=f"{item.get('total_required', '-')}", inline=True)

        view = PendingActionView(item)

        await interaction.channel.send(embed=embed, view=view)
