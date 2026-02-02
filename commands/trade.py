import random
import discord
from discord import app_commands
from discord.ui import View, Button

START_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978521375674621/371204A2-EAC5-487E-80E1-E409A2CDB31A.png"
UP_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978522042695700/56325194-FA0D-412A-91F0-9632A7FE6AE7.png"
DOWN_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978521715675238/56325194-FA0D-412A-91F0-9632A7FE6AE7.png"


class TradeView(View):
    def __init__(self, amount: int):
        super().__init__(timeout=60)
        self.amount = amount
        self.finished = False  # 👈 تشفير الصفقة

    @discord.ui.button(label="📈 صعود", style=discord.ButtonStyle.success)
    async def up(self, interaction: discord.Interaction, button: Button):
        await self.handle(interaction, "up")

    @discord.ui.button(label="📉 هبوط", style=discord.ButtonStyle.danger)
    async def down(self, interaction: discord.Interaction, button: Button):
        await self.handle(interaction, "down")

    async def handle(self, interaction: discord.Interaction, choice: str):
        # 🔒 لو الصفقة خلصت
        if self.finished:
            await interaction.response.send_message(
                "❌ الصفقة انتهت بالفعل",
                ephemeral=True
            )
            return

        self.finished = True  # 👈 قفل الصفقة

        result = random.choice(["up", "down"])
        win = choice == result

        embed = discord.Embed(
            title="**نتيجة التداول**",
            description=(
                f"**مبلغ الصفقة:** {self.amount}\n"
                f"**اختيارك:** {'صعود' if choice == 'up' else 'هبوط'}\n"
                f"**النتيجة:** {'صعود' if result == 'up' else 'هبوط'}\n\n"
                f"{'✅ كسبت' if win else '❌ خسرت'}"
            ),
            color=0x2ecc71 if win else 0xe74c3c
        )

        embed.set_image(url=UP_IMG if result == "up" else DOWN_IMG)

        # 👇 الرد الوحيد
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


@app_commands.command(name="trade", description="بدء صفقة تداول")
async def trade(interaction: discord.Interaction, amount: int):
    embed = discord.Embed(
        title="**ابدأ التداول**",
        description=f"**مبلغ الصفقة:** {amount}\n\nاختر الاتجاه 👇",
        color=0x3498db
    )
    embed.set_image(url=START_IMG)

    await interaction.response.send_message(
        embed=embed,
        view=TradeView(amount)
    )
