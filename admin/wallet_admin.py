import json
import os
from datetime import datetime

ADMIN_IDS = [
    802148738939748373,
    1035345058561540127
]

WALLET_FILE = "data/wallets.json"


def load_wallets():
    if not os.path.exists(WALLET_FILE):
        return {}
    with open(WALLET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_wallets(data):
    with open(WALLET_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_wallet(user_id: int):
    wallets = load_wallets()
    uid = str(user_id)

    if uid not in wallets:
        wallets[uid] = {
            "balance": 0,
            "total_deposit": 0,
            "total_profit": 0,
            "total_loss": 0,
            "last_update": str(datetime.now())
        }
        save_wallets(wallets)

    return wallets, wallets[uid]


def handle_admin_message(bot, message):
    if message.author.bot:
        return

    if message.author.id not in ADMIN_IDS:
        return

    content = message.content.strip().split()
    if not content:
        return

    command = content[0].lower()

    # ===== جاهز =====
    if command == "جاهز":
        bot.loop.create_task(message.channel.send("جاهز"))
        return

    # ===== ahelp =====
    if command == "ahelp":
        bot.loop.create_task(
            message.channel.send(
                "🛠 **أوامر الإدارة**\n\n"
                "`add @user amount` ➜ إضافة رصيد\n"
                "`remove @user amount` ➜ خصم رصيد\n"
                "`ahelp` ➜ عرض الأوامر\n"
                "`جاهز` ➜ اختبار",
                delete_after=10
            )
        )
        return

    # ===== add / remove =====
    if command in ("add", "remove"):
        if len(content) < 3 or not message.mentions:
            bot.loop.create_task(
                message.channel.send(
                    "❌ الصيغة الصحيحة: add @user amount",
                    delete_after=5
                )
            )
            return

        member = message.mentions[0]

        try:
            amount = int(content[2])
        except ValueError:
            bot.loop.create_task(
                message.channel.send("❌ المبلغ لازم يكون رقم", delete_after=5)
            )
            return

        wallets, wallet = get_wallet(member.id)

        if command == "add":
            wallet["balance"] += amount
            wallet["total_deposit"] += amount
            action = "➕ تم إضافة"
        else:
            if wallet["balance"] < amount:
                bot.loop.create_task(
                    message.channel.send("❌ رصيد غير كافي", delete_after=5)
                )
                return
            wallet["balance"] -= amount
            wallet["total_loss"] += amount
            action = "➖ تم خصم"

        wallet["last_update"] = str(datetime.now())
        save_wallets(wallets)

        bot.loop.create_task(
            message.channel.send(
                f"{action} `{amount}`\n"
                f"👤 {member.mention}\n"
                f"💼 الرصيد الحالي: `{wallet['balance']}`",
                delete_after=7
            )
        )
