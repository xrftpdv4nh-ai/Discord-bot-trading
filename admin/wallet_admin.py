import discord
from config import ADMIN_ROLE_ID
import json
import os
from datetime import datetime

WALLET_FILE = "data/wallets.json"

def load_wallets():
    if not os.path.exists(WALLET_FILE):
        return {}
    with open(WALLET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_wallets(data):
    with open(WALLET_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ✅ لازم async
async def handle_admin_message(bot, message: discord.Message):
    if message.author.bot or not message.guild:
        return

    # لازم رول أدمن
    if ADMIN_ROLE_ID not in [r.id for r in message.author.roles]:
        return

    args = message.content.strip().split()
    if not args:
        return

    cmd = args[0].lower()

# ================== ADD ==================
if cmd == "add" and len(args) == 3:
    if not message.mentions:
        await message.channel.send("❌ منشن المستخدم الأول")
        return

    try:
        amount = int(args[2])
        if amount <= 0:
            raise ValueError
    except:
        await message.channel.send("❌ المبلغ لازم يكون رقم أكبر من 0")
        return

    user = message.mentions[0]
    wallets = message.client.wallets

    await wallets.update_one(
        {"user_id": user.id},
        {
            "$inc": {
                "balance": amount,
                "total_deposit": amount
            },
            "$set": {
                "last_update": str(datetime.now())
            },
            "$setOnInsert": {
                "total_profit": 0,
                "total_loss": 0
            }
        },
        upsert=True
    )

    await message.channel.send(
        f"✅ تم إضافة **{amount}** نقطة لـ {user.mention}"
    )

# ================== REMOVE ==================
elif cmd == "remove" and len(args) == 3:
    if not message.mentions:
        await message.channel.send("❌ منشن المستخدم الأول")
        return

    try:
        amount = int(args[2])
        if amount <= 0:
            raise ValueError
    except:
        await message.channel.send("❌ المبلغ لازم يكون رقم أكبر من 0")
        return

    user = message.mentions[0]
    wallets = message.client.wallets

    wallet = await wallets.find_one({"user_id": user.id})

    if not wallet:
        await message.channel.send("❌ المستخدم ليس لديه محفظة")
        return

    new_balance = max(0, wallet.get("balance", 0) - amount)

    await wallets.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "balance": new_balance,
                "last_update": str(datetime.now())
            }
        }
    )

    await message.channel.send(
        f"🚫 تم خصم **{amount}** نقطة من {user.mention}"
    )

# ================== HELP ==================
elif cmd == "ahelp":
    await message.channel.send(
        "**🛠 أوامر الأدمن:**\n"
        "`add @user amount`\n"
        "`remove @user amount`\n"
        "`ahelp`"
    )

    # ================== HELP ==================
    elif cmd == "ahelp":
        await message.channel.send(
            "**🛠 أوامر الأدمن:**\n"
            "`add @user amount`\n"
            "`remove @user amount`\n"
            "`ahelp`"
        )
