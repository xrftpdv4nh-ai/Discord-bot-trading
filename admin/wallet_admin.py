from discord.ext import commands
import json
import os
from datetime import datetime

# ================== ADMIN IDS ==================
ADMIN_IDS = [
    802148738939748373,  # ايديك
    1035345058561540127
]

# ================== WALLET FILE ==================
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


class WalletAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, ctx):
        return ctx.author.id in ADMIN_IDS

    # ================== !add ==================
    @commands.command(name="add")
    async def add_balance(self, ctx, member: commands.MemberConverter, amount: int):
        if not self.is_admin(ctx):
            return

        if amount <= 0:
            await ctx.send("❌ **مبلغ غير صالح**", delete_after=5)
            return

        wallets, wallet = get_wallet(member.id)

        wallet["balance"] += amount
        wallet["total_deposit"] += amount
        wallet["last_update"] = str(datetime.now())

        save_wallets(wallets)

        await ctx.send(
            f"✅ **تم إضافة رصيد**\n"
            f"👤 {member.mention}\n"
            f"💰 المبلغ: `{amount}`\n"
            f"💼 الرصيد الحالي: `{wallet['balance']}`",
            delete_after=7
        )

    # ================== !remove ==================
    @commands.command(name="remove")
    async def remove_balance(self, ctx, member: commands.MemberConverter, amount: int):
        if not self.is_admin(ctx):
            return

        wallets, wallet = get_wallet(member.id)

        if amount <= 0 or wallet["balance"] < amount:
            await ctx.send("❌ **رصيد غير كافي أو مبلغ غير صحيح**", delete_after=5)
            return

        wallet["balance"] -= amount
        wallet["total_loss"] += amount
        wallet["last_update"] = str(datetime.now())

        save_wallets(wallets)

        await ctx.send(
            f"➖ **تم خصم رصيد**\n"
            f"👤 {member.mention}\n"
            f"💰 المبلغ: `{amount}`\n"
            f"💼 الرصيد الحالي: `{wallet['balance']}`",
            delete_after=7
        )

    # ================== !ahelp ==================
    @commands.command(name="ahelp")
    async def ahelp(self, ctx):
        if not self.is_admin(ctx):
            return

        await ctx.send(
            "🛠 **أوامر الإدارة**\n\n"
            "➕ `!add @user amount` ➜ إضافة رصيد\n"
            "➖ `!remove @user amount` ➜ خصم رصيد\n\n"
            "📌 هذه الأوامر خاصة بالإدارة فقط",
            delete_after=10
        )
