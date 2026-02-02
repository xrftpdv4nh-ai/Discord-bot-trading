import discord
from discord import app_commands
from discord.ui import View, Button
import random

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
        # تحديد نتيجة السوق تلقائي
        market_up = random.random() < BASE_WIN_RATE
        market_result = "UP" if market_up else "DOWN"

        win = user_choice == market_result

        if market_result == "UP":
            image = discord.File("assets/up.png")
            market_text = "📈 السهم صعد"
        else:
            image = discord.File("assets/down.png")
            market_text = "📉 السهم هبط"

        if win:
            result_text = f"✅ اختيارك صحيح\n💰 كسبت {int(self.amount * 0.8):,} نقطة"
        else:
            result_text = f"❌ اختيارك غلط\n💸 خسرت {self.amount:,} نقطة"

        await interaction.response.edit_message(
            content=f"{market_text}\n\n{result_text}",
            attachments=[image],
            view=None
        )


class UserCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="user", description="User trading commands")

    @app_commands.command(name="trade", description="ابدأ تداول")
    async def trade(self, interaction: discord.Interaction, amount: int):
        if amount < MIN_BET or amount > MAX_BET:
            await interaction.response.send_message(
                f"❌ المبلغ لازم يكون بين {MIN_BET:,} و {MAX_BET:,}",
                ephemeral=True
            )
            return

        file = discord.File("assets/start.png")
        view = TradeView(amount)

        await interaction.response.send_message(
            content=f"📊 مبلغ الصفقة: {amount:,} نقطة\nاختر اتجاه التداول 👇",
            file=file,
            view=view
        )
