import random
import discord
from discord import app_commands
from discord.ui import View, Button
from pathlib import Path

ASSETS = Path("assets")

START_IMG = ASSETS / "start.png"
UP_IMG = ASSETS / "up.png"
DOWN_IMG = ASSETS / "down.png"


class TradeView(View):
    def __init__(self, amount: int):
        super().__init__(timeout=30)
        self.amount = amount

    @discord.ui.button(label="صعود 📈", style=discord.ButtonStyle.success)
    async def up(self, interaction: discord.Interaction, button: Button):
        await self.handle_trade(interaction, "up")

    @discord.ui.button(label="هبوط 📉", style=discord.ButtonStyle.danger)
    async def down(self, interaction: discord.Interaction, button: Button):
        await self.handle_trade(interaction, "down")

    async def handle_trade(self, interaction: discord.Interaction, choice: str):
        result = random.choice(["up", "down"])
        win = choice == result

        emb = discord.Embed(
            title="**نتيجة التداول**",
            description=(
                f"**مبلغ الصفقة:** {self.amount}\n"
                f"**اختيارك:** {'صعود' if choice == 'up' else 'هبوط'}\n\n"
                f"{'✅ كسبت الصفقة' if win else '❌ خسرت الصفقة'}"
            ),
            color=0x2ecc71 if win else 0xe74c3c
        )

        image_path = UP_IMG if result == "up" else DOWN_IMG
        file = discord.File(image_path, filename="result.png")
        emb.set_image(url="attachment://result.png")

        self.disable_all_items()

        await interaction.response.edit_message(
            embed=emb,
            view=self,
            files=[file]   # ✅ الصح
        )


@app_commands.command(name="trade", description="بدء صفقة تداول")
@app_commands.describe(amount="مبلغ التداول")
async def trade(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message(
            "❌ المبلغ لازم يكون أكبر من 0",
            ephemeral=True
        )
        return

    emb = discord.Embed(
        title="**ابدأ التداول**",
        description=f"**مبلغ الصفقة:** {amount}\n\n👇 اختر اتجاه التداول",
        color=0x3498db
    )

    file = discord.File(START_IMG, filename="start.png")
    emb.set_image(url="attachment://start.png")

    await interaction.response.send_message(
        embed=emb,
        view=TradeView(amount),
        files=[file]   # ✅ الصح
    )
