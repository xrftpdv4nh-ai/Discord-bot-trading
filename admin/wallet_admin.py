from utils.json_db import load_json, save_json

WALLET_FILE = "data/wallets.json"


def add_balance(user_id: int, amount: int):
    """
    إضافة رصيد للمستخدم
    """
    wallets = load_json(WALLET_FILE, {})

    uid = str(user_id)
    if uid not in wallets:
        wallets[uid] = {
            "balance": 0,
            "total_deposit": 0
        }

    wallets[uid]["balance"] += amount
    wallets[uid]["total_deposit"] += amount

    save_json(WALLET_FILE, wallets)


# لو عندك أوامر أدمن نصية سيبها زي ما هي
async def handle_admin_message(bot, message):
    pass
