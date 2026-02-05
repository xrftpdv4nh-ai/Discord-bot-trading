import discord
import json, os
from datetime import datetime, timedelta
from config import ROLE_LOG_CHANNEL_ID

DATA_FILE = "data/role_subscriptions.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ===================== GIVE ROLE =====================
async def give_role(bot, member: discord.Member, role: discord.Role, admin):
    data = load_data()
    uid = str(member.id)

    now = datetime.utcnow()
    expires = now + timedelta(days=7)

    # لو عنده اشتراك قديم
    if uid in data:
        old_exp = datetime.fromisoformat(data[uid]["expires_at"])
        if old_exp > now:
            expires = old_exp + timedelta(days=7)

    await member.add_roles(role)

    data[uid] = {
        "role_id": role.id,
        "expires_at": expires.isoformat()
    }
    save_data(data)

    log = bot.get_channel(ROLE_LOG_CHANNEL_ID)
    if log:
        await log.send(
            f"✅ **Role Activated / Renewed**\n"
            f"👤 {member.mention}\n"
            f"🏷 {role.mention}\n"
            f"📅 Expires: `{expires.strftime('%Y-%m-%d %H:%M')}`\n"
            f"👮 By: {admin.mention}"
        )

# ===================== CHECK EXPIRED ROLES =====================
async def check_roles_task(bot: discord.Client):
    await bot.wait_until_ready()

    while not bot.is_closed():
        data = load_data()
        now = datetime.utcnow()
        changed = False

        for uid, info in list(data.items()):
            expires = datetime.fromisoformat(info["expires_at"])
            if expires <= now:
                guilds = bot.guilds
                for guild in guilds:
                    member = guild.get_member(int(uid))
                    if not member:
                        continue

                    role = guild.get_role(info["role_id"])
                    if role and role in member.roles:
                        await member.remove_roles(role)

                        log = bot.get_channel(ROLE_LOG_CHANNEL_ID)
                        if log:
                            await log.send(
                                f"⛔ **Role Expired**\n"
                                f"👤 {member.mention}\n"
                                f"🏷 {role.name}\n"
                                f"📅 Expired at: `{expires.strftime('%Y-%m-%d %H:%M')}`"
                            )

                del data[uid]
                changed = True

        if changed:
            save_data(data)

        await discord.utils.sleep_until(
            now + timedelta(minutes=5)
        )
