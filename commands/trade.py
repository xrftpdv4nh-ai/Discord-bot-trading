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
        await self.resolve(interaction, "UP")

    @discord.ui.button(label="📉 هبوط", style=discord.ButtonStyle.danger)
    async def down(self, interaction: discord.Interaction, button: Button):
        await self.resolve(interaction, "DOWN")

    async def resolve(self, interaction: discord.Interaction, choice: str):
        seed = secrets.randbelow(1_000_000) + int(time.time() * 1000)
        random.seed(seed)

        roll = random.randint(1, 100)
        market = "UP" if roll <= int(BASE_WIN_RATE * 100) else "DOWN"
        win = choice == market

        if market == "UP":
            image = discord.File("assets/up.png")
            market_text = "**📈 السهم صعد**"
        else:
            image = discord.File("assets/down.png")
            market_text = "**📉 السهم هبط**"

        if win:
            profit = int(self.amount * 0.8)
            result = f"**✅ اختيارك صحيح**\n**💰 ربحت {profit:,} نقطة**"
        else:
            result = f"**❌ اختيارك غلط**\n**💸 خسرت {self.amount:,} نقطة**"

        await interaction.response.edit_message(
            content=f"{market_text}\n\n{result}",
            attachments=[image],
            view=None
        )


class TradeCommand:
    def __init__(self):
        self.daily = {}

    def get_tier(self, member: discord.Member | None) -> str:
        if not member:
            return "user"

        ids = [r.id for r in member.roles]
        if VIP_ROLE_ID in ids:
            return "vip"
        if PRO_ROLE_ID in ids:
            return "pro"
        return "user"

    @app_commands.guild_only()
    @app_commands.command(name="trade", description="ابدأ تداول")
    async def trade(self, interaction: discord.Interaction, amount: int):
        try:
            await interaction.response.defer(ephemeral=True)

            user_id = interaction.user.id
            today = str(date.today())

            try:
                member = await interaction.guild.fetch_member(user_id)
            except:
                member = None

            tier = self.get_tier(member)
            cfg = TIERS[tier]

            if amount < cfg["min_bet"] or amount > cfg["max_bet"]:
                await interaction.followup.send(
                    f"**❌ المبلغ المسموح لمستوى {tier.upper()} من {cfg['min_bet']:,} إلى {cfg['max_bet']:,} نقطة**",
                    ephemeral=True
                )
                return

            data = self.daily.get(user_id, {"date": today, "count": 0})
            if data["date"] != today:
                data = {"date": today, "count": 0}

            if data["count"] >= cfg["daily_limit"]:
                await interaction.followup.send(
                    f"**⛔ وصلت للحد اليومي للتداول**\n\n"
                    f"**🔰 المستوى: {tier.upper()}**\n"
                    f"**🔢 الصفقات: {cfg['daily_limit']} / {cfg['daily_limit']}**\n"
                    f"**📆 تقدر تتداول تاني بكرة**",
                    ephemeral=True
                )
                return

            data["count"] += 1
            self.daily[user_id] = data

            file = discord.File("assets/start.png")
            view = TradeView(amount)

            await interaction.followup.send(
                content=(
                    f"**🔰 المستوى: {tier.upper()}**\n"
                    f"**📊 مبلغ الصفقة: {amount:,} نقطة**\n"
                    f"**🔢 صفقات اليوم: {data['count']} / {cfg['daily_limit']}**\n\n"
                    f"**اختر اتجاه التداول 👇**"
                ),
                file=file,
                view=view,
                ephemeral=True
            )

        except Exception as e:
            print("❌ TRADE ERROR:", e)
            try:
                await interaction.followup.send(
                    "**❌ حصل خطأ غير متوقع، حاول مرة تانية بعد شوية**",
                    ephemeral=True
                )
            except:
                pass
