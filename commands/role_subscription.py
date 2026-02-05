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

async def give_role(bot, member, role: discord.Role, admin):
    data = load_data()
    uid = str(member.id)

    now = datetime.utcnow()
    expires = now + timedelta(days=7)

    if uid in data:
        old_exp = datetime.fromisoformat(data[uid]["expires_at"])
        expires = max(old_exp, now) + timedelta(days=7)

    await member.add_roles(role)

    data[uid] = {
        "role_id": role.id,
        "expires_at": expires.isoformat()
    }
    save_data(data)

    log = bot.get_channel(ROLE_LOG_CHANNEL_ID)
    if log:
        await log.send(
            f"✅ **Role Activated**\n"
            f"👤 {member.mention}\n"
            f"🏷 {role.name}\n"
            f"📅 Expires: `{expires}`\n"
            f"👮 By: {admin.mention}"
        )
