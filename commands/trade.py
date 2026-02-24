import random
import discord
from discord import app_commands
from discord.ui import View, Button
from datetime import date, datetime
import json
import os

# ================== IMAGES ==================
START_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978521375674621/371204A2-EAC5-487E-80E1-E409A2CDB31A.png"
UP_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978522042695700/56325194-FA0D-412A-91F0-9632A7FE6AE7.png"
DOWN_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978521715675238/56325194-FA0D-412A-91F0-9632A7FE6AE7.png"

# ================== ROLES ==================
PRO_ROLE_ID = 1467922966485668118
VIP_ROLE_ID = 1467923207389712556

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

# ================== TEMP STORAGE ==================
user_data = {}

def get_user_level(member: discord.Member):
    roles = [r.id for r in member.roles]

    if VIP_ROLE_ID in roles:
        return {"name": "VIP", "min": 3000, "max": 70000, "win_rate": 0.56, "profit_rate": 0.88, "daily_limit": 35}
    elif PRO_ROLE_ID in roles:
        return {"name": "PRO", "min": 3000, "max": 40000, "win_rate": 0.54, "profit_rate": 0.80, "daily_limit": 20}
    else:
        return {"name": "USER", "min": 3000, "max": 12000, "win_rate": 0.52, "profit_rate": 0.78, "daily_limit": 12}

# ================== VIEW ==================
class TradeView(View):
    def __init__(self, amount: int, user_id: int, level: dict):
        super().__init__(timeout=60)
        self.amount = amount
        self.user_id = user_id
        self.level = level
        self.finished = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "⛔ **هذه الصفقة ليست لك**",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="📈 صعود", style=discord.ButtonStyle.success)
    async def up(self, interaction: discord.Interaction, button: Button):
        await self.handle(interaction, "up")

    @discord.ui.button(label="📉 هبوط", style=discord.ButtonStyle.danger)
    async def down(self, interaction: discord.Interaction, button: Button):
        await self.handle(interaction, "down")

    async def handle(self, interaction: discord.Interaction, choice: str):
        if self.finished:
            await interaction.response.send_message(
                "⛔ **الصفقة انتهت بالفعل**",
                ephemeral=True
            )
            return

        self.finished = True
        data = user_data[self.user_id]
        wallets, wallet = get_wallet(self.user_id)

        # ===== منع 3 مكاسب ورا بعض =====
        forced_lose = data["win_streak"] >= 2
        win_rate = self.level["win_rate"]

        if data["profit_today"] >= 40000:
            win_rate -= 0.18
        elif data["profit_today"] >= 20000:
            win_rate -= 0.08

        if forced_lose:
            result = "down" if choice == "up" else "up"
        else:
            result = choice if random.random() < win_rate else ("down" if choice == "up" else "up")

        win = (choice == result)

        if win:
            data["win_streak"] += 1
            profit = int(self.amount * self.level["profit_rate"])
            data["profit_today"] += profit
            wallet["balance"] += profit
            wallet["total_profit"] += profit
            result_text = f"🎉 **ربحت:** `{profit}`"
        else:
            data["win_streak"] = 0
            wallet["balance"] -= self.amount
            wallet["total_loss"] += self.amount
            result_text = f"💥 **خسرت:** `{self.amount}`"

        data["trades_today"] += 1
        wallet["last_update"] = str(datetime.now())
        save_wallets(wallets)

        embed = discord.Embed(
            title="📊 **نتيجة الصفقة**",
            description=(
                f"🏷️ **مستواك:** `{self.level['name']}`\n"
                f"💰 **قيمة الصفقة:** `{self.amount}`\n"
                f"🧭 **اختيارك:** `{'صعود 📈' if choice == 'up' else 'هبوط 📉'}`\n"
                f"📉 **حركة السوق:** `{'صعود 📈' if result == 'up' else 'هبوط 📉'}`\n\n"
                f"{result_text}\n\n"
                f"💼 **رصيدك الحالي:** `{wallet['balance']}`"
            ),
            color=0x2ecc71 if win else 0xe74c3c
        )

        embed.set_image(url=UP_IMG if result == "up" else DOWN_IMG)

        await interaction.response.send_message(embed=embed)

# ================== COMMAND ==================
@app_commands.command(name="trade", description="بدء صفقة تداول")
@app_commands.describe(amount="مبلغ التداول")
async def trade(interaction: discord.Interaction, amount: int):
    member = interaction.user
    level = get_user_level(member)
    uid = member.id
    today = str(date.today())

    wallets, wallet = get_wallet(uid)

    if wallet["balance"] < amount:
        await interaction.response.send_message(
            f"⛔ **رصيد غير كافي**\n💼 **رصيدك الحالي:** `{wallet['balance']}`",
            ephemeral=True
        )
        return

    if uid not in user_data or user_data[uid]["date"] != today:
        user_data[uid] = {"date": today, "trades_today": 0, "profit_today": 0, "win_streak": 0}

    data = user_data[uid]

    if data["trades_today"] >= level["daily_limit"]:
        await interaction.response.send_message(
            f"⛔ **تم إيقاف التداول اليومي**\n📊 **الحد الأقصى:** `{level['daily_limit']}`",
            ephemeral=True
        )
        return

    if amount < level["min"] or amount > level["max"]:
        await interaction.response.send_message(
            f"⛔ **مبلغ غير مسموح**\n🔻 `{level['min']}` | 🔺 `{level['max']}`",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🚀 **بدء صفقة تداول**",
        description=(
            f"🏷️ **مستواك:** `{level['name']}`\n"
            f"💰 **مبلغ الصفقة:** `{amount}`\n"
            f"💼 **رصيدك:** `{wallet['balance']}`\n\n"
            "📊 **اختر اتجاه السوق:**"
        ),
        color=0x3498db
    )
    embed.set_image(url=START_IMG)

    await interaction.response.send_message(
        embed=embed,
        view=TradeView(amount, uid, level)
    )
