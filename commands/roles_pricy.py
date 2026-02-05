import discord
from discord import app_commands
from config import SUPPORT_ROLE_ID  # حط ID رول الـ support هنا

# ===================== IDs =====================
PRO_ROLE_ID = 1467922966485668118
VIP_ROLE_ID = 1467923207389712556

PRICE_IMAGE = "https://media.discordapp.net/attachments/1293146258516607008/1468761676802166900/9F20178E-DDF8-47A7-B1F3-38015838E2B9.png"

# ===================== CHECK =====================
def support_only(interaction: discord.Interaction) -> bool:
    return SUPPORT_ROLE_ID in [r.id for r in interaction.user.roles]

# ===================== ENGLISH =====================
@app_commands.command(name="e-sale", description="Show Trono Bot premium role prices")
async def e_sale(interaction: discord.Interaction):
    if not support_only(interaction):
        await interaction.response.send_message(
            "❌ You are not allowed to use this command.",
            ephemeral=True
        )
        return

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

    await interaction.response.send_message(embed=embed)

# ===================== ARABIC =====================
@app_commands.command(name="a-sale", description="عرض أسعار رولات Trono Bot")
async def a_sale(interaction: discord.Interaction):
    if not support_only(interaction):
        await interaction.response.send_message(
            "❌ لا تملك صلاحية استخدام هذا الأمر",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="💎 Trono Bot – الرولات المميزة",
        description=(
            "**طوّر تجربتك داخل السيرفر مع رولات Trono Bot المدفوعة.**\n\n"
            "**🟦 رول PRO (لمدة 7 أيام)**\n"
            "• اشتراك أسبوعي\n"
            "• دعم فني أسرع\n"
            "• مميزات تداول متقدمة\n"
            "• أولوية في تنفيذ الطلبات\n\n"
            "**💰 السعر:**\n"
            "• 40 جنيه (فودافون / إنستاباي)\n"
            "• 100,000 نقطة ProBot\n\n"
            "────────────────────\n\n"
            "**🟪 رول VIP (لمدة 7 أيام)**\n"
            "• اشتراك أسبوعي\n"
            "• أعلى أولوية دعم\n"
            "• وصول كامل للتداول\n"
            "• مميزات VIP حصرية\n\n"
            "**💰 السعر:**\n"
            "• 80 جنيه (فودافون / إنستاباي)\n"
            "• 220,000 نقطة ProBot\n\n"
            "_للاشتراك تواصل مع الدعم._"
        ),
        color=0xf1c40f
    )

    embed.set_image(url=PRICE_IMAGE)
    embed.set_footer(text="Trono Bot • نظام الرولات")

    await interaction.response.send_message(embed=embed)
