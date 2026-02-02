import discord
from discord import app_commands

# ===== ADMIN IDS =====
ADMIN_IDS = [
    802148738939748373,
    1035345058561540127
]

@app_commands.command(
    name="embed",
    description="إرسال Embed قابل للتعديل (أدمن فقط)"
)
async def embed(
    interaction: discord.Interaction,
    title: str,
    description: str,
    color: str,
    image_url: str = None
):
    # تحقق إن المستخدم أدمن
    if interaction.user.id not in ADMIN_IDS:
        await interaction.response.send_message(
            "❌ الأمر ده للأدمن فقط",
            ephemeral=True
        )
        return

    # تحويل اللون من HEX
    try:
        embed_color = int(color.replace("#", ""), 16)
    except:
        embed_color = 0x2ecc71  # لون افتراضي

    emb = discord.Embed(
        title=title,
        description=description,
        color=embed_color
    )

    # صورة اختيارية
    if image_url:
        emb.set_image(url=image_url)

    await interaction.response.send_message(embed=emb)
