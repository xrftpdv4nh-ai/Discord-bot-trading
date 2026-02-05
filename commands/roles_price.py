import discord
from config import SUPPORT_ROLE_ID

# ===================== ROLE IDs =====================
PRO_ROLE_ID = 1467922966485668118
VIP_ROLE_ID = 1467923207389712556

PRICE_IMAGE = "https://media.discordapp.net/attachments/1293146258516607008/1468761676802166900/9F20178E-DDF8-47A7-B1F3-38015838E2B9.png"

# ===================== CHECK =====================
def has_support_role(member: discord.Member) -> bool:
    return any(role.id == SUPPORT_ROLE_ID for role in member.roles)

# ===================== HANDLER =====================
async def handle_sale_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    content = message.content.lower().strip()

    # Support only
    if not has_support_role(message.author):
        return

    # ===================== ENGLISH =====================
    if content == "e-sale":
        embed = discord.Embed(
            title="💎 Trono Bot – Premium Role Pricing",
            description=(
                "**Unlock the full power of Trono Bot with premium roles.**\n"
                "Designed for serious traders who want higher limits,\n"
                "better profits, and priority handling.\n\n"

                f"🟦 **<@&{PRO_ROLE_ID}> — PRO Role (7 Days)**\n"
                "• Weekly subscription\n"
                "• Increased trading limits\n"
                "• Higher daily trade count\n"
                "• Improved profit rates\n"
                "• Priority support\n\n"
                "**💰 Price:**\n"
                "• 40 EGP (Vodafone / InstaPay)\n"
                "• 100,000 ProBot credits\n\n"
                "────────────────────\n\n"
                f"🟪 **<@&{VIP_ROLE_ID}> — VIP Role (7 Days)**\n"
                "• Weekly subscription\n"
                "• Maximum trading limits\n"
                "• Highest profit rates\n"
                "• Maximum daily trades\n"
                "• Fastest request & deposit handling\n"
                "• Full priority support\n\n"
                "**💰 Price:**\n"
                "• 80 EGP (Vodafone / InstaPay)\n"
                "• 220,000 ProBot credits\n\n"
                "_Contact support to activate your role._"
            ),
            color=0x9b59b6
        )

        embed.set_image(url=PRICE_IMAGE)
        embed.set_footer(text="Trono Bot • Premium Trading System")

        await message.channel.send(embed=embed)

        # 🧹 delete user message
        try:
            await message.delete()
        except:
            pass

    # ===================== ARABIC =====================
    elif content == "a-sale":
        embed = discord.Embed(
            title="💎 Trono Bot – أسعار الرولات المميزة",
            description=(
                "**فعّل أقوى مميزات Trono Bot مع الرولات المدفوعة.**\n"
                "مخصصة للمتداولين الجادين الباحثين عن\n"
                "حدود أعلى وأرباح أفضل وسرعة تنفيذ.\n\n"

                f"🟦 **<@&{PRO_ROLE_ID}> — رول PRO (7 أيام)**\n"
                "• اشتراك أسبوعي\n"
                "• زيادة حدود التداول\n"
                "• عدد صفقات يومية أكبر\n"
                "• نسبة أرباح أفضل\n"
                "• أولوية في الدعم الفني\n\n"
                "**💰 السعر:**\n"
                "• 40 جنيه (فودافون / إنستاباي)\n"
                "• 100,000 نقطة ProBot\n\n"
                "────────────────────\n\n"
                f"🟪 **<@&{VIP_ROLE_ID}> — رول VIP (7 أيام)**\n"
                "• اشتراك أسبوعي\n"
                "• أعلى حد تداول في السيرفر\n"
                "• أعلى نسبة أرباح\n"
                "• أكبر عدد صفقات يومية\n"
                "• أسرع تنفيذ للطلبات والشحن\n"
                "• دعم فني بأولوية قصوى\n\n"
                "**💰 السعر:**\n"
                "• 80 جنيه (فودافون / إنستاباي)\n"
                "• 220,000 نقطة ProBot\n\n"
                "_للاشتراك تواصل مع الدعم._"
            ),
            color=0xf1c40f
        )

        embed.set_image(url=PRICE_IMAGE)
        embed.set_footer(text="Trono Bot • نظام الرولات المميزة")

        await message.channel.send(embed=embed)

        # 🧹 delete user message
        try:
            await message.delete()
        except:
            pass
