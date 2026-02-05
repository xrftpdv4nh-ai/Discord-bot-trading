import discord
import json
import os
from datetime import datetime, timedelta
from config import ROLE_LOG_CHANNEL_ID

DATA_FILE = "data/role_subscriptions.json"

# ===================== DATA =====================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ===================== GIVE ROLE =====================
async def give_role(bot, member: discord.Member, role: discord.Role, admin: discord.Member):
    data = load_data()
    uid = str(member.id)

    now = datetime.utcnow()
    expires = now + timedelta(days=7)
    renewed = False

    # لو عنده اشتراك قبل كده → تجديد
    if uid in data and data[uid]["role_id"] == role.id:
        try:
            old_exp = datetime.fromisoformat(data[uid]["expires_at"])
            expires = max(old_exp, now) + timedelta(days=7)
            renewed = True
        except:
            expires = now + timedelta(days=7)

    # إعطاء الرول
    await member.add_roles(role, reason="Role subscription")

    # حفظ الداتا
    data[uid] = {
        "role_id": role.id,
        "expires_at": expires.isoformat()
    }
    save_data(data)

    # ===================== LOG =====================
    log_channel = bot.get_channel(ROLE_LOG_CHANNEL_ID)
    if not log_channel:
        return

    if renewed:
        await log_channel.send(
            f"🔄 **Role Renewed**\n"
            f"👤 User: {member.mention}\n"
            f"🏷 Role: **{role.name}**\n"
            f"📅 New Expiry: `{expires.strftime('%Y-%m-%d %H:%M UTC')}`\n"
            f"👮 Renewed By: {admin.mention}"
        )
    else:
        await log_channel.send(
            f"✅ **Role Activated**\n"
            f"👤 User: {member.mention}\n"
            f"🏷 Role: **{role.name}**\n"
            f"📅 Expires: `{expires.strftime('%Y-%m-%d %H:%M UTC')}`\n"
            f"👮 Activated By: {admin.mention}"
        )
