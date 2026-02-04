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

def handle_admin_message(bot, message: discord.Message):
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
            message.channel.send("❌ منشن المستخدم الأول")
            return

        try:
            amount = int(args[2])
        except:
            message.channel.send("❌ المبلغ لازم يكون رقم")
            return

        user = message.mentions[0]
        wallets = load_wallets()
        uid = str(user.id)

        if uid not in wallets or not isinstance(wallets[uid], dict):
            wallets[uid] = {
                "balance": 0,
                "total_deposit": 0,
                "total_profit": 0,
                "total_loss": 0,
                "last_update": ""
            }

        wallets[uid]["balance"] += amount
        wallets[uid]["total_deposit"] += amount
        wallets[uid]["last_update"] = str(datetime.now())

        save_wallets(wallets)

        message.channel.send(
            f"✅ تم إضافة **{amount}** نقطة لـ {user.mention}"
        )

    # ================== REMOVE ==================
    elif cmd == "remove" and len(args) == 3:
        if not message.mentions:
            message.channel.send("❌ منشن المستخدم الأول")
            return

        try:
            amount = int(args[2])
        except:
            message.channel.send("❌ المبلغ لازم يكون رقم")
            return

        user = message.mentions[0]
        wallets = load_wallets()
        uid = str(user.id)

        if uid not in wallets:
            message.channel.send("❌ المستخدم ليس لديه محفظة")
            return

        wallets[uid]["balance"] = max(0, wallets[uid]["balance"] - amount)
        wallets[uid]["last_update"] = str(datetime.now())

        save_wallets(wallets)

        message.channel.send(
            f"🚫 تم خصم **{amount}** نقطة من {user.mention}"
        )

    # ================== HELP ==================
    elif cmd == "ahelp":
        message.channel.send(
            "**🛠 أوامر الأدمن:**\n"
            "`add @user amount`\n"
            "`remove @user amount`\n"
            "`ahelp`"
        )
