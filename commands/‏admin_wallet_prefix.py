import discord
from discord.ext import commands
import json
import os
from datetime import datetime

# ================== ADMIN IDS ==================
ADMIN_IDS = [
    802148738939748373,
    1035345058561540127
]

# ================== WALLET ==================
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


class AdminWallet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================== !addbalance ==================
    @commands.command(name="addbalance")
    async def addbalance(self, ctx, member: discord.Member, amount: int):
        if ctx.author.id not in ADMIN_IDS:
            return

        if amount <= 0:
            await ctx.send("❌ مبلغ غير صالح", delete_after=5)
            return

        wallets, wallet = get_wallet(member.id)

        wallet["balance"] += amount
        wallet["total_deposit"] += amount
        wallet["last_update"] = str(datetime.now())

        save_wallets(wallets)

        await ctx.send(
            f"✅ **تم إضافة الرصيد**\n"
            f"👤 {member.mention}\n"
            f"💰 المبلغ: `{amount}`\n"
            f"💼 الرصيد الحالي: `{wallet['balance']}`",
            delete_after=7
        )

    # ================== !removebalance ==================
    @commands.command(name="removebalance")
    async def removebalance(self, ctx, member: discord.Member, amount: int):
        if ctx.author.id not in ADMIN_IDS:
            return

        wallets, wallet = get_wallet(member.id)

        if amount <= 0 or wallet["balance"] < amount:
            await ctx.send("❌ رصيد غير كافي أو مبلغ غير صحيح", delete_after=5)
            return

        wallet["balance"] -= amount
        wallet["total_loss"] += amount
        wallet["last_update"] = str(datetime.now())

        save_wallets(wallets)

        await ctx.send(
            f"🧾 **تم خصم الرصيد**\n"
            f"👤 {member.mention}\n"
            f"💰 المبلغ: `{amount}`\n"
            f"💼 الرصيد الحالي: `{wallet['balance']}`",
            delete_after=7
        )

    # ================== !setbalance ==================
    @commands.command(name="setbalance")
    async def setbalance(self, ctx, member: discord.Member, amount: int):
        if ctx.author.id not in ADMIN_IDS:
            return

        if amount < 0:
            await ctx.send("❌ رقم غير صالح", delete_after=5)
            return

        wallets, wallet = get_wallet(member.id)

        wallet["balance"] = amount
        wallet["last_update"] = str(datetime.now())

        save_wallets(wallets)

        await ctx.send(
            f"⚙️ **تم تعيين الرصيد**\n"
            f"👤 {member.mention}\n"
            f"💼 الرصيد الجديد: `{wallet['balance']}`",
            delete_after=7
        )

    # ================== !help ==================
    @commands.command(name="help")
    async def help(self, ctx):
        if ctx.author.id not in ADMIN_IDS:
            return

        message = (
            "🛠 **أوامر الإدارة**\n\n"
            "➕ `!addbalance @user amount`\n"
            "➖ `!removebalance @user amount`\n"
            "⚙️ `!setbalance @user amount`\n\n"
            "📌 هذه الأوامر خاصة بالإدارة فقط"
        )

        await ctx.send(message, delete_after=10)
