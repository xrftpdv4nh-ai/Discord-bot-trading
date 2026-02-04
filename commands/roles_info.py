import discord

# ===== ROLES =====
SUPPORT_ROLE_ID = 1468746308780294266
PRO_ROLE_ID = 1467922966485668118
VIP_ROLE_ID = 1467923207389712556

IMAGE_URL = "https://media.discordapp.net/attachments/1293146258516607008/1468748992434143422/5313DBA3-6822-49CC-9BA8-4D42BAA92178.png"


def has_support_role(member: discord.Member) -> bool:
    return any(role.id == SUPPORT_ROLE_ID for role in member.roles)


async def handle_roles_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    # السماح فقط لرول Support
    if not has_support_role(message.author):
        return

    cmd = message.content.lower().strip()

    # ================== ENGLISH ==================
    if cmd == "e-role":
        embed = discord.Embed(
            title="💎 Premium Trading Roles",
            description=(
                "**Upgrade your trading experience and unlock advanced features.**\n\n"
                "Our premium roles are built for traders who want better limits,\n"
                "higher profits, and a professional trading environment.\n\n"

                "**Available Roles:**\n"
                f"🔹 <@&{PRO_ROLE_ID}> — **PRO Trader**\n"
                f"🔹 <@&{VIP_ROLE_ID}> — **VIP Trader**\n\n"

                "**PRO Role Benefits:**\n"
                "• Higher trading limits\n"
                "• More daily trades\n"
                "• Better profit percentage\n"
                "• Faster deposit review\n"
                "• Priority support\n\n"

                "**VIP Role Benefits:**\n"
                "• Maximum trading limits\n"
                "• Highest profit percentage\n"
                "• Maximum daily trades\n"
                "• Fastest deposit approval\n"
                "• Full priority support\n"
                "• Exclusive trading advantages\n\n"

                "**Important Notice:**\n"
                "Any abuse, rule violation, or system exploitation\n"
                "may result in permanent role removal."
            ),
            color=0x2ecc71
        )

        embed.set_image(url=IMAGE_URL)
        embed.set_footer(text="Trade smarter • Trade faster • Trade premium")

        await message.channel.send(embed=embed)

    # ================== ARABIC ==================
    elif cmd == "a-role":
        embed = discord.Embed(
            title="💎 رولات التداول المميزة",
            description=(
                "**ارتقِ بتجربة التداول الخاصة بك وافتح مميزات أقوى.**\n\n"
                "الرولات المميزة مخصصة للمتداولين الجادين\n"
                "الذين يبحثون عن حدود أعلى وأرباح أفضل وسرعة أكبر.\n\n"

                "**الرولات المتاحة:**\n"
                f"🔹 <@&{PRO_ROLE_ID}> — **PRO**\n"
                f"🔹 <@&{VIP_ROLE_ID}> — **VIP**\n\n"

                "**مميزات رول PRO:**\n"
                "• حد تداول أعلى\n"
                "• عدد صفقات يومية أكبر\n"
                "• نسبة أرباح أفضل\n"
                "• سرعة في مراجعة الشحن\n"
                "• أولوية في الدعم الفني\n\n"

                "**مميزات رول VIP:**\n"
                "• أعلى حد تداول في السيرفر\n"
                "• أعلى نسبة أرباح\n"
                "• أكبر عدد صفقات يومية\n"
                "• أسرع قبول للشحن\n"
                "• دعم فني كامل بأولوية قصوى\n"
                "• مميزات تداول حصرية\n\n"

                "**تنبيه مهم:**\n"
                "إساءة استخدام النظام أو مخالفة قوانين السيرفر\n"
                "قد تؤدي إلى سحب الرول نهائيًا."
            ),
            color=0xf1c40f
        )

        embed.set_image(url=IMAGE_URL)
        embed.set_footer(text="تداول بذكاء • تداول بأمان • تداول باحتراف")

        await message.channel.send(embed=embed)
