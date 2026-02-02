import discord
from discord import app_commands
from discord.ui import View, Button
import random


class TradeView(View):
    def __init__(self, amount: int):
        super().__init__(timeout=30)
        self.amount = amount

    @discord.ui.button(label="📈 صعود", style=discord.ButtonStyle.success)
    async def up(self, interaction: discord.Interaction, button: Button):
        await self.handle(interaction, "up")

    @discord.ui.button(label="📉 هبوط", style=discord.ButtonStyle.danger)
    async def down(self, interaction: discord.Interaction, button: Button):
        await self.handle(interaction, "down")

    async def handle(self, interaction: discord.Interaction, choice: str):
        # 👇 هنا الاتجاهات
        result = random.choice(["up", "down"])

        if choice == result:
            msg = f"✅ **كسبت**\nاختيارك: {choice}\nالنتيجة: {result}"
        else:
            msg = f"❌ **خسرت**\nاختيارك: {choice}\nالنتيجة: {result}"

        # 👇 رد مباشر وواضح على الزر
        await interaction.response.send_message(
            msg,
            ephemeral=True
        )


@app_commands.command(name="trade", description="اختبار زرار التداول")
async def trade(interaction: discord.Interaction, amount: int):
    await interaction.response.send_message(
        f"**مبلغ الصفقة:** {amount}\nاختار الاتجاه 👇",
        view=TradeView(amount)
    )
