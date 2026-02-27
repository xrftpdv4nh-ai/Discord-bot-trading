import random
import discord
from discord import app_commands
from discord.ui import View, Button
from datetime import date, datetime

# ================== IMAGES ==================
START_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978521375674621/371204A2-EAC5-487E-80E1-E409A2CDB31A.png"
UP_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978522042695700/56325194-FA0D-412A-91F0-9632A7FE6AE7.png"
DOWN_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978521715675238/56325194-FA0D-412A-91F0-9632A7FE6AE7.png"

# ================== ROLES ==================
PRO_ROLE_ID = 1467922966485668118
VIP_ROLE_ID = 1467923207389712556

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
            await interaction.response.send_message("⛔ هذه الصفقة ليست لك", ephemeral=True)
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
            await interaction.response.send_message("⛔ الصفقة انتهت", ephemeral=True)
            return

        self.finished = True

        wallets = interaction.client.wallets
        wallet = await wallets.find_one({"user_id": self.user_id})

        if not wallet:
            await interaction.response.send_message("⛔ خطأ في المحفظة", ephemeral=True)
            return

        data = user_data[self.user_id]

        # ================== قراءة النسبة من Mongo ==================
        settings = await interaction.client.db.settings.find_one({"type": "global_trade"})
        win_rate_percent = settings["win_rate"] if settings else int(self.level["win_rate"] * 100)

        user_setting = await interaction.client.db.settings.find_one({
            "type": "user_trade",
            "user_id": self.user_id
        })

        if user_setting:
            win_rate_percent = user_setting["win_rate"]

        win_rate = win_rate_percent / 100

        # ================== نظامك القديم ==================
        forced_lose = data["win_streak"] >= 2

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

            await wallets.update_one(
                {"user_id": self.user_id},
                {
                    "$inc": {
                        "balance": profit,
                        "total_profit": profit
                    },
                    "$set": {"last_update": str(datetime.now())}
                }
            )

            result_text = f"🎉 ربحت `{profit}`"
            color = 0x2ecc71

        else:
            data["win_streak"] = 0

            await wallets.update_one(
                {"user_id": self.user_id},
                {
                    "$inc": {
                        "balance": -self.amount,
                        "total_loss": self.amount
                    },
                    "$set": {"last_update": str(datetime.now())}
                }
            )

            result_text = f"💥 خسرت `{self.amount}`"
            color = 0xe74c3c

        data["trades_today"] += 1

        updated_wallet = await wallets.find_one({"user_id": self.user_id})

        embed = discord.Embed(
            title="📊 نتيجة الصفقة",
            description=(
                f"🏷️ مستواك: `{self.level['name']}`\n"
                f"💰 مبلغ الصفقة: `{self.amount}`\n"
                f"🧭 اختيارك: `{'صعود 📈' if choice == 'up' else 'هبوط 📉'}`\n"
                f"📉 حركة السوق: `{'صعود 📈' if result == 'up' else 'هبوط 📉'}`\n\n"
                f"{result_text}\n\n"
                f"💼 رصيدك الحالي: `{updated_wallet.get('balance', 0)}`"
            ),
            color=color
        )

        embed.set_image(url=UP_IMG if result == "up" else DOWN_IMG)

        await interaction.response.send_message(embed=embed)


# ================== COMMAND ==================
@app_commands.command(name="trade", description="بدء صفقة تداول")
@app_commands.describe(amount="مبلغ التداول")
async def trade(interaction: discord.Interaction, amount: int):

    wallets = interaction.client.wallets
    uid = interaction.user.id

    wallet = await wallets.find_one({"user_id": uid})

    if not wallet:
        wallet = {
            "user_id": uid,
            "balance": 0,
            "total_deposit": 0,
            "total_profit": 0,
            "total_loss": 0,
            "last_update": str(datetime.now())
        }
        await wallets.insert_one(wallet)

    level = get_user_level(interaction.user)
    today = str(date.today())

    if wallet["balance"] < amount:
        await interaction.response.send_message(
            f"⛔ رصيد غير كافي\nرصيدك الحالي: `{wallet['balance']}`",
            ephemeral=True
        )
        return

    if uid not in user_data or user_data[uid]["date"] != today:
        user_data[uid] = {"date": today, "trades_today": 0, "profit_today": 0, "win_streak": 0}

    data = user_data[uid]

    if data["trades_today"] >= level["daily_limit"]:
        await interaction.response.send_message(
            f"⛔ تم إيقاف التداول اليومي\nالحد الأقصى: `{level['daily_limit']}`",
            ephemeral=True
        )
        return

    if amount < level["min"] or amount > level["max"]:
        await interaction.response.send_message(
            f"⛔ مبلغ غير مسموح\n🔻 `{level['min']}` | 🔺 `{level['max']}`",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🚀 بدء صفقة تداول",
        description=(
            f"🏷️ مستواك: `{level['name']}`\n"
            f"💰 مبلغ الصفقة: `{amount}`\n"
            f"💼 رصيدك: `{wallet['balance']}`\n\n"
            "📊 اختر اتجاه السوق:"
        ),
        color=0x3498db
    )

    embed.set_image(url=START_IMG)

    await interaction.response.send_message(
        embed=embed,
        view=TradeView(amount, uid, level)
    )
