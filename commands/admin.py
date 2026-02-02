import discord
from discord import app_commands

# ===== ADMIN IDS =====
ADMIN_IDS = [
    802148738939748373,
    1035345058561540127
]


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AdminCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="admin", description="Admin commands")

    @app_commands.command(
        name="embed",
        description="إرسال Embed مخصص (أدمن فقط)"
    )
    async def embed(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        color: str,
        image_url: str = None
    ):
        # تحقق من الأدمن
        if not is_admin(interaction.user.id):
            await interaction.response.send_message(
                "❌ الأمر ده للأدمن فقط",
                ephemeral=True
            )
            return

        # تحويل اللون من Hex
        try:
            embed_color = int(color.replace("#", ""), 16)
        except:
            embed_color = 0x2ecc71  # لون افتراضي أخضر

        embed = discord.Embed(
            title=title,
            description=description,
            color=embed_color
        )

        embed.set_footer(text=f"By {interaction.user.name}")

        if image_url:
            embed.set_image(url=image_url)

        await interaction.response.send_message(embed=embed)
