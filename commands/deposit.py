import discord
from discord import app_commands
from datetime import datetime
import math

from config import (
    DEPOSIT_CHANNEL_ID,
    PROBOT_FEE_RATE,
    PROBOT_RECEIVER_ID,
    DEPOSIT_TIMEOUT
)


# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد عبر ProBot")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):

    # التحقق من الروم
    if interaction.channel.id != DEPOSIT_CHANNEL_ID:
        await interaction.response.send_message(
            "🚫 هذا الروم مخصص للشحن فقط."
        )
        return

    # التحقق من القيمة
    if points <= 0:
        await interaction.response.send_message(
            "❌ عدد النقاط يجب أن يكون أكبر من صفر."
        )
        return

    # حساب المبلغ المطلوب تحويله (يشمل الضريبة)
    total_required = math.ceil(points / (1 - PROBOT_FEE_RATE))

    # تخزين العملية في قاعدة البيانات
    await interaction.client.pending.insert_one({
        "user_id": interaction.user.id,
        "points": points,
        "total_required": total_required,
        "status": "waiting_transfer",
        "channel_id": interaction.channel.id,
        "created_at": datetime.utcnow()
    })

    # إنشاء الإيمبد
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

    embed.add_field(
        name="⏳ المهلة",
        value=f"```{DEPOSIT_TIMEOUT} دقائق```",
        inline=False
    )

    embed.set_footer(text="سيتم إضافة النقاط تلقائيًا بعد استلام التحويل")

    await interaction.response.send_message(embed=embed)
