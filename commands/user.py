import discord
from discord import app_commands
from discord.ui import View, Button
import random
import time
import secrets

from config import MIN_BET, MAX_BET, BASE_WIN_RATE


class TradeView(View):
    def __init__(self, amount: int):
        super().__init__(timeout=60)
        self.amount = amount

    @discord.ui.button(label="📈 صعود", style=discord.ButtonStyle.success)
    async def up(self, interaction: discord.Interaction, button: Button):
        await self.handle_trade(interaction, user_choice="UP")

    @discord.ui.button(label="📉 هبوط", style=discord.ButtonStyle.danger)
    async def down(self, interaction: discord.Interaction, button: Button):
        await self.handle_trade(interaction, user_choice="DOWN")

    async def handle_trade(self, interaction: discord.Interaction, user_choice: str):
        # ===== عشوائية قوية (كسر أي Pattern) =====
        seed = secrets.randbelow(1_000_000) + int(time.time() * 1000)
        random.seed(seed)

        roll = random.randint(1, 100)
        market_result = "UP" if roll <= int(BASE_WIN_RATE * 100) else "DOWN"

        win = (user_choice == market_result)

        # ===== اختيار الصورة حسب نتيجة السوق =====
        if market_result == "UP":
            image = discord.File("assets/up.png")
            market_text = "**📈 السهم صعد**"
        else:
            image = discord.File("assets/down.png")
            market_text = "**📉 السهم هبط**"

        # ===== نص النتيجة =====
        if win:
            result_text = f"**✅ اختيارك صحيح\n💰 كسبت {int(self.amount * 0.8):,} نقطة**"
        else:
            result_text = f"**❌ اختيارك غلط\n💸 خسرت {self.amount:,} نقطة**"

        await interaction.response.edit_message(
            content=f"{market_text}\n\n{result_text}",
            attachments=[image],
            view=None
        )


class UserCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="user", description="User trading commands")

    @app_commands.command(name="trade", description="**ابدأ تداول**")
    async def trade(self, interaction: discord.Interaction, amount: int):
        if amount < MIN_BET or amount > MAX_BET:
            await interaction.response.send_message(
                f"**❌ المبلغ لازم يكون بين {MIN_BET:,} و {MAX_BET:,}**",
                ephemeral=True
            )
            return

        file = discord.File("assets/start.png")
        view = TradeView(amount)

        await interaction.response.send_message(
            content=f"**📊 مبلغ الصفقة: {amount:,} نقطة\nاختر اتجاه التداول 👇**",
            file=file,
            view=view
        )
