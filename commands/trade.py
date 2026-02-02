import random
import discord
from discord import app_commands
from discord.ui import View, Button
from datetime import date

# ===== IMAGE URLS =====
START_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978521375674621/371204A2-EAC5-487E-80E1-E409A2CDB31A.png"
UP_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978522042695700/56325194-FA0D-412A-91F0-9632A7FE6AE7.png"
DOWN_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978521715675238/56325194-FA0D-412A-91F0-9632A7FE6AE7.png"

# ===== ROLE IDS =====
PRO_ROLE_ID = 1467922966485668118
VIP_ROLE_ID = 1467923207389712556

# ===== STORAGE (مؤقت – لحد ما نركب Wallet) =====
user_data = {}

def get_user_level(member: discord.Member):
    roles = [r.id for r in member.roles]

    if VIP_ROLE_ID in roles:
        return {
            "name": "VIP",
            "min": 3000,
            "max": 70000,
            "win_rate": 0.60,
            "profit_rate": 0.90,
            "daily_limit": 35
        }
    elif PRO_ROLE_ID in roles:
        return {
            "name": "PRO",
            "min": 3000,
            "max": 40000,
            "win_rate": 0.56,
            "profit_rate": 0.85,
            "daily_limit": 20
        }
    else:
        return {
            "name": "USER",
            "min": 3000,
            "max": 12000,
            "win_rate": 0.53,
            "profit_rate": 0.80,
            "daily_limit": 12
        }


class TradeView(View):
    def __init__(self, amount: int, interaction: discord.Interaction, level: dict):
        super().__init__(timeout=60)
        self.amount = amount
        self.user_id = interaction.user.id
        self.level = level

    @discord.ui.button(label="📈 صعود", style=discord.ButtonStyle.success)
    async def up(self, interaction: discord.Interaction, button: Button):
        await self.handle(interaction, "up")

    @discord.ui.button(label="📉 هبوط", style=discord.ButtonStyle.danger)
    async def down(self, interaction: discord.Interaction, button: Button):
        await self.handle(interaction, "down")

    async def handle(self, interaction: discord.Interaction, choice: str):
        uid = self.user_id
        today = str(date.today())

        data = user_data[uid]

        # 🔒 منع 3 مكاسب ورا بعض
        forced_lose = data["win_streak"] >= 2

        win_rate = self.level["win_rate"]

        # 📉 تقليل الحظ مع المكسب العالي
        if data["profit_today"] >= 40000:
            win_rate -= 0.18
        elif data["profit_today"] >= 20000:
            win_rate -= 0.08

        win = False
        if not forced_lose and random.random() < win_rate:
            win = True

        # ===== النتيجة =====
        if win:
            data["win_streak"] += 1
            profit = int(self.amount * self.level["profit_rate"])
            data["profit_today"] += profit
            result_text = f"🎉 **ربحت:** `{profit}`"
            img = UP_IMG
        else:
            data["win_streak"] = 0
            profit = -self.amount
            result_text = f"💥 **خسرت:** `{self.amount}`"
            img = DOWN_IMG

        data["trades_today"] += 1

        embed = discord.Embed(
            title="📊 **نتيجة الصفقة**",
            description=(
                f"🏷️ **المستوى:** `{self.level['name']}`\n"
                f"💰 **قيمة الصفقة:** `{self.amount}`\n"
                f"🧭 **اختيارك:** `{'صعود 📈' if choice == 'up' else 'هبوط 📉'}`\n\n"
                f"{result_text}"
            ),
            color=0x2ecc71 if win else 0xe74c3c
        )
        embed.set_image(url=img)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


@app_commands.command(name="trade", description="بدء صفقة تداول")
@app_commands.describe(amount="مبلغ التداول")
async def trade(interaction: discord.Interaction, amount: int):
    member = interaction.user
    level = get_user_level(member)

    uid = member.id
    today = str(date.today())

    if uid not in user_data or user_data[uid]["date"] != today:
        user_data[uid] = {
            "date": today,
            "trades_today": 0,
            "profit_today": 0,
            "win_streak": 0
        }

    data = user_data[uid]

    # ❌ ليمت الصفقات
    if data["trades_today"] >= level["daily_limit"]:
        await interaction.response.send_message(
            f"⛔ **وصلت للحد الأقصى للصفقات اليومية ({level['daily_limit']})**",
            ephemeral=True
        )
        return

    # ❌ حد أدنى / أقصى
    if amount < level["min"]:
        await interaction.response.send_message(
            f"❌ **الحد الأدنى للتداول هو {level['min']}**",
            ephemeral=True
        )
        return

    if amount > level["max"]:
        await interaction.response.send_message(
            f"❌ **الحد الأقصى لمستواك هو {level['max']}**",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🚀 **بدء صفقة تداول**",
        description=(
            f"🏷️ **المستوى:** `{level['name']}`\n"
            f"💰 **مبلغ الصفقة:** `{amount}`\n\n"
            "📊 **اختر اتجاه السوق:**"
        ),
        color=0x3498db
    )
    embed.set_image(url=START_IMG)

    await interaction.response.send_message(
        embed=embed,
        view=TradeView(amount, interaction, level)
    )
