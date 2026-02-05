import discord
from config import ADMIN_ROLE_ID, ROLE_LOG_CHANNEL_ID
from commands.role_subscription import give_role
from datetime import datetime

# ===================== ROLE IDS =====================
PRO_ROLE_ID = 1467922966485668118
VIP_ROLE_ID = 1467923207389712556


def is_admin(member: discord.Member) -> bool:
    return any(role.id == ADMIN_ROLE_ID for role in member.roles)


async def handle_admin_role_message(bot, message: discord.Message):
    if message.author.bot or not message.guild:
        return

    # صلاحية الأدمن
    if not is_admin(message.author):
        return

    args = message.content.lower().split()
    if not args or not message.mentions:
        return

    command = args[0]
    member = message.mentions[0]
    guild = message.guild
    log_channel = guild.get_channel(ROLE_LOG_CHANNEL_ID)

    # ===================== GIVE PRO =====================
    if command == "give-pro":
        role = guild.get_role(PRO_ROLE_ID)
        if not role:
            await message.channel.send("❌ رول PRO غير موجود")
            return

        await give_role(bot, member, role, message.author)

        await message.channel.send(
            f"✅ تم إعطاء رول **PRO** لـ {member.mention}"
        )

    # ===================== GIVE VIP =====================
    elif command == "give-vip":
        role = guild.get_role(VIP_ROLE_ID)
        if not role:
            await message.channel.send("❌ رول VIP غير موجود")
            return

        await give_role(bot, member, role, message.author)

        await message.channel.send(
            f"✅ تم إعطاء رول **VIP** لـ {member.mention}"
        )

    # ===================== REMOVE ROLE =====================
    elif command == "remove-role":
        removed = False

        for role_id in (PRO_ROLE_ID, VIP_ROLE_ID):
            role = guild.get_role(role_id)
            if role and role in member.roles:
                await member.remove_roles(role)
                removed = True

                if log_channel:
                    await log_channel.send(
                        f"🚫 **Role Removed Manually**\n"
                        f"👤 {member.mention}\n"
                        f"🏷 {role.mention}\n"
                        f"👮 By: {message.author.mention}\n"
                        f"📅 `{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}`"
                    )

        if removed:
            await message.channel.send(
                f"🚫 تم سحب الرول من {member.mention}"
            )
        else:
            await message.channel.send(
                "ℹ️ المستخدم لا يمتلك رول PRO أو VIP"
            )
