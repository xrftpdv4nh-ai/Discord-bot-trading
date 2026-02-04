import discord
from config import ADMIN_ROLE_ID
from utils.json_db import load_json, save_json

WALLET_FILE = "data/wallets.json"


# ========================
# أدوات مساعدة
# ========================

def get_balance(user_id: int) -> int:
    wallets = load_json(WALLET_FILE, {})
    return int(wallets.get(str(user_id), 0))


def add_balance(user_id: int, amount: int):
    wallets = load_json(WALLET_FILE, {})
    uid = str(user_id)

    current = int(wallets.get(uid, 0))
    wallets[uid] = current + int(amount)

    save_json(WALLET_FILE, wallets)


def remove_balance(user_id: int, amount: int) -> bool:
    wallets = load_json(WALLET_FILE, {})
    uid = str(user_id)

    current = int(wallets.get(uid, 0))
    if current < amount:
        return False

    wallets[uid] = current - int(amount)
    save_json(WALLET_FILE, wallets)
    return True


# ========================
# أوامر الأدمن النصية
# ========================

async def handle_admin_message(bot, message: discord.Message):
    if message.author.bot:
        return

    # تأكد إن اللي بيكلم أدمن
    if not any(role.id == ADMIN_ROLE_ID for role in message.author.roles):
        return

    content = message.content.strip().split()

    if not content:
        return

    cmd = content[0].lower()

    # !add @user amount
    if cmd == "!add" and len(content) == 3:
        try:
            user = message.mentions[0]
            amount = int(content[2])

            add_balance(user.id, amount)
            await message.reply(f"✅ تم إضافة **{amount}** نقطة لـ {user.mention}")

        except:
            await message.reply("❌ الاستخدام الصحيح: `!add @user amount`")

    # !remove @user amount
    elif cmd == "!remove" and len(content) == 3:
        try:
            user = message.mentions[0]
            amount = int(content[2])

            if remove_balance(user.id, amount):
                await message.reply(f"🗑️ تم خصم **{amount}** نقطة من {user.mention}")
            else:
                await message.reply("❌ الرصيد غير كافي")

        except:
            await message.reply("❌ الاستخدام الصحيح: `!remove @user amount`")

    # !balance @user
    elif cmd == "!balance" and len(content) == 2:
        try:
            user = message.mentions[0]
            bal = get_balance(user.id)
            await message.reply(f"💰 رصيد {user.mention}: **{bal}** نقطة")

        except:
            await message.reply("❌ الاستخدام الصحيح: `!balance @user`")
