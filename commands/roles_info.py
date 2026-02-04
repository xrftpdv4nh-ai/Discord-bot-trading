import discord

SUPPORT_ROLE_ID = 1468746308780294266
IMAGE_URL = "https://media.discordapp.net/attachments/1293146258516607008/1468748992434143422/5313DBA3-6822-49CC-9BA8-4D42BAA92178.png"

def has_support_role(member: discord.Member):
    return any(role.id == SUPPORT_ROLE_ID for role in member.roles)

async def handle_roles_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    if not has_support_role(message.author):
        return

    cmd = message.content.lower().strip()

    # ================== ENGLISH ==================
    if cmd == "e-role":
        embed = discord.Embed(
            title="💼 **Trading Roles & Benefits**",
            description=(
                "**Upgrade your experience and unlock premium features**\n\n"
                "🔹 <@&ROLE_ID_1>\n"
                "- Priority support\n"
                "- Faster trade processing\n"
                "- Exclusive trading channels\n\n"
                "🔹 <@&ROLE_ID_2>\n"
                "- Higher deposit limits\n"
                "- Special trade signals\n"
                "- Access to VIP offers\n\n"
                "📌 *Choose the role that fits your trading goals.*"
            ),
            color=0x2ecc71
        )
        embed.set_image(url=IMAGE_URL)
        embed.set_footer(text="Professional Trading System")

        await message.channel.send(embed=embed)

    # ================== ARABIC ==================
    elif cmd == "a-role":
        embed = discord.Embed(
            title="💼 **رولات التداول والمميزات**",
            description=(
                "**طوّر تجربتك وافتح مميزات حصرية**\n\n"
                "🔹 <@&ROLE_ID_1>\n"
                "- دعم أسرع\n"
                "- تنفيذ تداولات بأولوية\n"
                "- رومات تداول خاصة\n\n"
                "🔹 <@&ROLE_ID_2>\n"
                "- حد إيداع أعلى\n"
                "- إشارات تداول مميزة\n"
                "- عروض حصرية\n\n"
                "📌 *اختار الرول اللي يناسب هدفك في التداول.*"
            ),
            color=0x3498db
        )
        embed.set_image(url=IMAGE_URL)
        embed.set_footer(text="نظام تداول احترافي")

        await message.channel.send(embed=embed)
