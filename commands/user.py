import discord
from discord import app_commands
from discord.ui import View, Button
import random
import time
import secrets
from datetime import date

from config import BASE_WIN_RATE

# ===== ROLE IDS =====
PRO_ROLE_ID = 1467922966485668118
VIP_ROLE_ID = 1467923207389712556

# ===== TIERS SETTINGS =====
TIERS = {
    "user": {
        "min_bet": 1,
        "max_bet": 12000,
        "daily_limit": 12
    },
    "pro": {
        "min_bet": 15000,
        "max_bet": 40000,
        "daily_limit": 20
    },
    "vip": {
        "min_bet": 5000,
        "max_bet": 70000,
        "daily_limit": 35
    }
}


class TradeView(View):
    def __init__(self, amount: int):
        super().__init__(timeout=60)
        self.amount = amount

    @discord.ui.button(label="📈 صعود", style=discord.ButtonStyle.success)
    async def up(self, interaction: discord.Interaction, button: Button):
        await self.handle_trade(interaction, "UP")

    @discord.ui.button(label="📉 هبوط", style=discord.ButtonStyle.danger)
    async def down(self, interaction: discord.Interaction, button: Button):
        await self.handle_trade(interaction, "DOWN")

    async def handle_trade(self, interaction: discord.Interaction, user_choice: str):
        # ===== عشوائية حقيقية =====
        seed = secrets.randbelow(1_000_000) + int(time.time() * 1000)
        random.seed(seed)

        roll = random.randint(1, 100)
        market_result = "UP" if roll <= int(BASE_WIN_RATE * 100) else "DOWN"
        win = user_choice == market_result

        # ===== صورة السوق =====
        if market_result == "UP":
            image = discord.File("assets/up.png")
            market_text = "**📈 السهم صعد**"
        else:
            image = discord.File("assets/down.png")
            market_text = "**📉 السهم هبط**"

        # ===== نتيجة الصفقة =====
        if win:
            profit = int(self.amount * 0.8)
            result_text = (
                "**✅ اختيارك صحيح**\n"
                f"**💰 ربحت {profit:,} نقطة**"
            )
        else:
            result_text = (
                "**❌ اختيارك غلط**\n"
                f"**💸 خسرت {self.amount:,} نقطة**"
            )

        await interaction.response.edit_message(
            content=f"{market_text}\n\n{result_text}",
            attachments=[image],
            view=None
        )


class TradeCommand:
    def __init__(self):
        # تخزين الصفقات اليومية تلقائي (RAM)
        self.daily_trades = {}

    def get_user_tier(self, member: discord.Member) -> str:
        role_ids = [role.id for role in member.roles]

        if VIP_ROLE_ID in role_ids:
            return "vip"
        if PRO_ROLE_ID in role_ids:
            return "pro"
        return "user"

    @app_commands.command(name="trade", description="ابدأ تداول")
    async def trade(self, interaction: discord.Interaction, amount: int):
        user_id = interaction.user.id
        today = str(date.today())

        member = interaction.guild.get_member(user_id)
        tier = self.get_user_tier(member)
        settings = TIERS[tier]

        min_bet = settings["min_bet"]
        max_bet = settings["max_bet"]
        daily_limit = settings["daily_limit"]

        # ===== التحقق من المبلغ =====
        if amount < min_bet or amount > max_bet:
            await interaction.response.send_message(
                f"**❌ المبلغ المسموح لمستوى {tier.upper()} من {min_bet:,} إلى {max_bet:,} نقطة**",
                ephemeral=True
            )
            return

        # ===== إدارة الصفقات اليومية (تلقائي) =====
        user_data = self.daily_trades.get(
            user_id, {"date": today, "count": 0}
        )

        if user_data["date"] != today:
            user_data = {"date": today, "count": 0}

        if user_data["count"] >= daily_limit:
            await interaction.response.send_message(
                f"**⛔ وصلت للحد اليومي للتداول**\n\n"
                f"**🔰 المستوى: {tier.upper()}**\n"
                f"**🔢 الصفقات: {daily_limit} / {daily_limit}**\n"
                f"**📆 تقدر تتداول تاني بكرة**",
                ephemeral=True
            )
            return

        user_data["count"] += 1
        self.daily_trades[user_id] = user_data

        # ===== شاشة البداية =====
        file = discord.File("assets/start.png")
        view = TradeView(amount)

        await interaction.response.send_message(
            content=(
                f"**🔰 المستوى: {tier.upper()}**\n"
                f"**📊 مبلغ الصفقة: {amount:,} نقطة**\n"
                f"**🔢 صفقات اليوم: {user_data['count']} / {daily_limit}**\n\n"
                f"**اختر اتجاه التداول 👇**"
            ),
            file=file,
            view=view
        )
