import random
import discord
from discord import app_commands
from discord.ui import View, Button

# ===== IMAGE URLS =====
START_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978521375674621/371204A2-EAC5-487E-80E1-E409A2CDB31A.png"
UP_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978522042695700/56325194-FA0D-412A-91F0-9632A7FE6AE7.png"
DOWN_IMG = "https://cdn.discordapp.com/attachments/1293146258516607008/1467978521715675238/56325194-FA0D-412A-91F0-9632A7FE6AE7.png"


class TradeView(View):
    def __init__(self, amount: int):
        super().__init__(timeout=30)
        self.amount = amount
        self.finished = False

    @discord.ui.button(label="📈 صعود", style=discord.ButtonStyle.success)
    async def up(self, interaction: discord.Interaction, button: Button):
        await self.finish(interaction, "up")

    @discord.ui.button(label="📉 هبوط", style=discord.ButtonStyle.danger)
    async def down(self, interaction: discord.Interaction, button: Button):
        await self.finish(interaction, "down")

    async def finish(self, interaction: discord.Interaction, choice: str):
        # حماية من الضغط أكتر من مرة
        if self.finished:
            await interaction.response.send_message(
                "❌ الصفقة خلصت بالفعل",
                ephemeral=True
            )
            return

        self.finished = True

        # نتيجة عشوائية
        result = random.choice(["up", "down"])
        win = choice == result

        # 1️⃣ نقفل الزراير في رسالة البداية
        self.disable_all_items()
        await interaction.response.edit_message(view=self)

        # 2️⃣ رسالة النتيجة (Only you can see)
        embed = discord.Embed(
            title="**نتيجة التداول**",
            description=(
                f"**مبلغ الصفقة:** {self.amount}\n"
                f"**اختيارك:** {'صعود' if choice == 'up' else 'هبوط'}\n"
                f"**النتيجة:** {'صعود' if result == 'up' else 'هبوط'}\n\n"
                f"{'✅ كسبت الصفقة' if win else '❌ خسرت الصفقة'}"
            ),
            color=0x2ecc71 if win else 0xe74c3c
        )

        embed.set_image(url=UP_IMG if result == "up" else DOWN_IMG)

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
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

    embed = discord.Embed(
        title="**ابدأ التداول**",
        description=f"**مبلغ الصفقة:** {amount}\n\n👇 اختر الاتجاه",
        color=0x3498db
    )
    embed.set_image(url=START_IMG)

    await interaction.response.send_message(
        embed=embed,
        view=TradeView(amount)
    )
