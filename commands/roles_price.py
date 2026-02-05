import discord
from discord import app_commands
from config import SUPPORT_ROLE_ID

# ===================== IDs =====================
PRO_ROLE_ID = 1467922966485668118
VIP_ROLE_ID = 1467923207389712556

PRICE_IMAGE = "https://media.discordapp.net/attachments/1293146258516607008/1468761676802166900/9F20178E-DDF8-47A7-B1F3-38015838E2B9.png"

# ===================== CHECK =====================
def has_support_role(member: discord.Member) -> bool:
    return SUPPORT_ROLE_ID in [r.id for r in member.roles]

# =================================================
# =============== SLASH COMMANDS ==================
# =================================================

@app_commands.command(name="e-sale", description="Show Trono Bot premium role prices")
async def e_sale(interaction: discord.Interaction):
    if not has_support_role(interaction.user):
        await interaction.response.send_message(
            "❌ You are not allowed to use this command.",
            ephemeral=True
        )
        return

    embed = build_embed_en()
    await interaction.response.send_message(embed=embed)


@app_commands.command(name="a-sale", description="عرض أسعار رولات Trono Bot")
async def a_sale(interaction: discord.Interaction):
    if not has_support_role(interaction.user):
        await interaction.response.send_message(
            "❌ لا تملك صلاحية استخدام هذا الأمر",
            ephemeral=True
        )
        return

    embed = build_embed_ar()
    await interaction.response.send_message(embed=embed)

# =================================================
# ============ MESSAGE COMMANDS ===================
# =================================================

async def handle_sale_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    if message.content.lower() != "a-sale":
        return

    if not has_support_role(message.author):
        await message.channel.send("❌ هذا الأمر مخصص لفريق الدعم فقط.")
        return

    embed = build_embed_ar()
    await message.channel.send(embed=embed)


async def handle_e_sale_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    if message.content.lower() != "e-sale":
        return

    if not has_support_role(message.author):
        await message.channel.send("❌ This command is for support team only.")
        return

    embed = build_embed_en()
    await message.channel.send(embed=embed)

# =================================================
# ================== EMBEDS =======================
# =================================================

def build_embed_en() -> discord.Embed:
    embed = discord.Embed(
        title="💎 Trono Bot – Premium Roles",
        description=(
            "**Upgrade your experience with Trono Bot premium roles.**\n\n"
            "**🟦 PRO Role (7 Days)**\n"
            "• Weekly subscription\n"
            "• Priority support\n"
            "• Advanced trading features\n"
            "• Faster request handling\n\n"
            "**💰 Price:**\n"
            "• 40 EGP (Vodafone / InstaPay)\n"
            "• 100,000 ProBot credits\n\n"
            "────────────────────\n\n"
            "**🟪 VIP Role (7 Days)**\n"
            "• Weekly subscription\n"
            "• Highest priority support\n"
            "• Full trading access\n"
            "• Exclusive VIP features\n\n"
            "**💰 Price:**\n"
            "• 80 EGP (Vodafone / InstaPay)\n"
            "• 220,000 ProBot credits\n\n"
            "_Contact support to subscribe._"
        ),
        color=0x9b59b6
    )

    embed.set_image(url=PRICE_IMAGE)
    embed.set_footer(text="Trono Bot • Premium System")
    return embed


def build_embed_ar() -> discord.Embed:
    embed = discord.Embed(
        title="💎 Trono Bot – الرولات المميزة",
        description=(
            "**طوّر تجربتك داخل السيرفر مع اشتراكات Trono Bot الأسبوعية.**\n\n"
            "**🟦 رول PRO (7 أيام)**\n"
            "• دعم فني أسرع\n"
            "• مراجعة أسرع للإيداع\n"
            "• مميزات تداول متقدمة\n\n"
            "**💰 السعر:**\n"
            "• 40 جنيه (فودافون / إنستاباي)\n"
            "• 100,000 بروبوت\n\n"
            "────────────────────\n\n"
            "**🟪 رول VIP (7 أيام)**\n"
            "• أعلى أولوية دعم\n"
            "• مراجعة فورية\n"
            "• وصول كامل للتداول\n"
            "• مميزات VIP حصرية\n\n"
            "**💰 السعر:**\n"
            "• 80 جنيه (فودافون / إنستاباي)\n"
            "• 220,000 بروبوت\n\n"
            "_للاشتراك تواصل مع الدعم._"
        ),
        color=0xf1c40f
    )

    embed.set_image(url=PRICE_IMAGE)
    embed.set_footer(text="Trono Bot • نظام الرولات")
    return embed
