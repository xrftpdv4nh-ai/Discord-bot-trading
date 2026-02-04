from utils.json_db import load_json, save_json

WALLET_FILE = "data/wallets.json"


def add_balance(user_id: int, amount: int):
    """
    إضافة رصيد (نقاط) للمستخدم
    """
    wallets = load_json(WALLET_FILE, {})
    uid = str(user_id)

    if uid not in wallets:
        wallets[uid] = {
            "balance": 0,
            "total_earned": 0
        }

    wallets[uid]["balance"] += int(amount)
    wallets[uid]["total_earned"] += int(amount)

    save_json(WALLET_FILE, wallets)


def remove_balance(user_id: int, amount: int):
    """
    خصم رصيد من المستخدم
    """
    wallets = load_json(WALLET_FILE, {})
    uid = str(user_id)

    if uid not in wallets:
        return False

    if wallets[uid]["balance"] < amount:
        return False

    wallets[uid]["balance"] -= int(amount)
    save_json(WALLET_FILE, wallets)
    return True


def get_balance(user_id: int):
    """
    جلب رصيد المستخدم
    """
    wallets = load_json(WALLET_FILE, {})
    uid = str(user_id)

    if uid not in wallets:
        return 0

    return wallets[uid].get("balance", 0)
