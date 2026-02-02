import discord
from discord import app_commands

# ===== ADMIN IDS =====
ADMIN_IDS = [
    802148738939748373,
    1035345058561540127
]

@app_commands.command(
    name="clear",
    description="مسح آخر 30 رسالة (أدمن فقط)"
)
async def clear(interaction: discord.Interaction):
    # تحقق من الأدمن
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message(
            "⛔ **هذا الأمر مخصص للإدارة فقط**",
            ephemeral=True
        )
        return

    channel = interaction.channel

    # رد سريع علشان Discord ما يعلّقش
    await interaction.response.defer(ephemeral=True)

    # مسح آخر 30 رسالة
    deleted = await channel.purge(limit=30)

    # تأكيد
    await interaction.followup.send(
        f"🧹 **تم مسح {len(deleted)} رسالة بنجاح**",
        ephemeral=True
    )
