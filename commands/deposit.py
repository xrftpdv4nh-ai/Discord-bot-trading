import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import uuid

from config import ADMIN_ACTION_CHANNEL_ID

# ========= View الأزرار =========
class DepositActionView(View):
    def __init__(self, user_id: int, amount: int):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.amount = amount

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            f"✅ تم قبول الإيداع وإضافة {self.amount} نقطة",
            ephemeral=True
        )
        await interaction.message.edit(view=None)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            "❌ تم رفض الإيداع",
            ephemeral=True
        )
        await interaction.message.edit(view=None)

# ========= Slash Command =========
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(amount="عدد النقاط")
async def deposit(interaction: discord.Interaction, amount: int):
    await interaction.response.send_message(
        f"📎 ابعت صورة إثبات التحويل **كرسالة عادية** في نفس الروم",
        ephemeral=True
    )

    # نحفظ الطلب مؤقتًا على اليوزر
    interaction.client.pending_deposits[interaction.user.id] = {
        "amount": amount,
        "interaction": interaction
    }

# ========= التقاط صورة الإثبات =========
async def handle_proof_message(message: discord.Message):
    bot = message.guild.me._state._get_client()

    if not message.attachments:
        return

    user_id = message.author.id
    if user_id not in bot.pending_deposits:
        return

    data = bot.pending_deposits.pop(user_id)
    amount = data["amount"]

    admin_channel = bot.get_channel(ADMIN_ACTION_CHANNEL_ID)
    if not admin_channel:
        return

    attachment = message.attachments[0]
    file = await attachment.to_file()

    embed = discord.Embed(
        title="📥 طلب إيداع جديد",
        color=discord.Color.gold()
    )
    embed.add_field(name="المستخدم", value=message.author.mention, inline=False)
    embed.add_field(name="المبلغ", value=str(amount), inline=False)

    view = DepositActionView(user_id, amount)

    await admin_channel.send(
        embed=embed,
        file=file,
        view=view
    )

    await message.delete()
    await message.channel.send(
        "⏳ تم استلام الإثبات، جاري المراجعة",
        delete_after=5
    )
