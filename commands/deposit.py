import discord
from discord import app_commands
from discord.ui import View, Button
from datetime import datetime
import math

from config import (
    DEPOSIT_CHANNEL_ID,
    PROBOT_FEE_RATE,
    PROBOT_RECEIVER_ID,
    DEPOSIT_TIMEOUT
)


# ================== VIEW ==================
class DepositView(View):
    def __init__(self, points: int, total_required: int):
        super().__init__(timeout=DEPOSIT_TIMEOUT * 60)
        self.points = points
        self.total_required = total_required

    @discord.ui.button(label="💳 بدء التحويل عبر ProBot", style=discord.ButtonStyle.primary)
    async def start_transfer(self, interaction: discord.Interaction, button: Button):

        await interaction.response.send_message(
            f"🔔 {interaction.user.mention}\n"
            f"قم بتحويل:\n"
            f"```{self.total_required:,} Credits```\n"
            f"إلى الحساب:\n"
            f"<@{PROBOT_RECEIVER_ID}>\n\n"
            f"⏳ لديك {DEPOSIT_TIMEOUT} دقائق لإتمام التحويل.",
        )

    @discord.ui.button(label="✅ تأكيد الإضافة", style=discord.ButtonStyle.success)
    async def confirm_add(self, interaction: discord.Interaction, button: Button):

        pending = interaction.client.pending
        wallets = interaction.client.wallets

        data = await pending.find_one({
            "user_id": interaction.user.id,
            "status": "ready_to_confirm"
        })

        if not data:
            await interaction.response.send_message(
                "❌ لم يتم استلام التحويل بعد أو انتهت المهلة.",
            )
            return

        # إضافة النقاط
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

        await pending.delete_one({"_id": data["_id"]})

        embed = discord.Embed(
            title="💎 TRONO DEPOSIT COMPLETED",
            color=0x2ecc71
        )

        embed.add_field(
            name="👤 المستخدم",
            value=interaction.user.mention,
            inline=False
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

        await interaction.response.send_message(embed=embed)


# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد عبر ProBot")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):

    if interaction.channel.id != DEPOSIT_CHANNEL_ID:
        await interaction.response.send_message(
            "🚫 هذا الروم مخصص للشحن فقط.",
        )
        return

    if points <= 0:
        await interaction.response.send_message(
            "❌ عدد النقاط يجب أن يكون أكبر من صفر.",
        )
        return

    # ✅ الحساب الصح بدون كسور
    total_required = math.ceil(points / (1 - PROBOT_FEE_RATE))

    # تخزين العملية
    await interaction.client.pending.insert_one({
        "user_id": interaction.user.id,
        "points": points,
        "total_required": total_required,
        "status": "waiting_transfer",
        "created_at": datetime.utcnow()
    })

    embed = discord.Embed(
        title="🚀 TRONO PROBOT DEPOSIT",
        description="━━━━━━━━━━━━━━━━━━",
        color=0x3498db
    )

    embed.add_field(
        name="👤 المستخدم",
        value=interaction.user.mention,
        inline=False
    )

    embed.add_field(
        name="💎 النقاط المطلوبة",
        value=f"```{points:,}```",
        inline=True
    )

    embed.add_field(
        name="🧾 رسوم ProBot",
        value=f"```{int(PROBOT_FEE_RATE * 100)}%```",
        inline=True
    )

    embed.add_field(
        name="💳 المطلوب تحويله",
        value=f"```{total_required:,} Credits```",
        inline=False
    )

    embed.add_field(
        name="🏦 الحساب المستلم",
        value=f"<@{PROBOT_RECEIVER_ID}>",
        inline=False
    )

    embed.set_footer(text="بعد التحويل اضغط تأكيد الإضافة")

    await interaction.response.send_message(
        embed=embed,
        view=DepositView(points, total_required),
    )
