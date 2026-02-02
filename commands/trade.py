import discord
from discord import app_commands
from discord.ui import View, Button
import random

from config import BASE_WIN_RATE


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
        market = "UP" if random.random() <= BASE_WIN_RATE else "DOWN"
        win = (choice == market)

        if market == "UP":
            image = discord.File("assets/up.png")
            text = "**📈 السهم صعد**"
        else:
            image = discord.File("assets/down.png")
            text = "**📉 السهم هبط**"

        if win:
            result = f"**✅ كسبت {int(self.amount * 0.8):,} نقطة**"
        else:
            result = f"**❌ خسرت {self.amount:,} نقطة**"

        await interaction.response.edit_message(
            content=f"{text}\n\n{result}",
            attachments=[image],
            view=None
        )


class TradeCommand:
    @app_commands.guild_only()
    @app_commands.command(name="trade", description="ابدأ تداول")
    async def trade(self, interaction: discord.Interaction, amount: int):
        if amount <= 0 or amount > 12000:
            await interaction.response.send_message(
                "**❌ الحد الأقصى للتداول هو 12,000 نقطة**",
                ephemeral=True
            )
            return

        file = discord.File("assets/start.png")
        view = TradeView(amount)

        await interaction.response.send_message(
            content=(
                f"**📊 مبلغ الصفقة: {amount:,} نقطة**\n"
                f"**اختر اتجاه التداول 👇**"
            ),
            file=file,
            view=view,
            ephemeral=True
        )
