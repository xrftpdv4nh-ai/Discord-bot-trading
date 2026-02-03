import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import uuid

from config import (
    ADMIN_ACTION_CHANNEL_ID,
    VODAFONE_NUMBER,
    INSTAPAY_NUMBER,
    PROBOT_OWNER_ID
)

# =========================
# View اختيار طريقة الدفع
# =========================
class PaymentMethodView(View):
    def __init__(self, user: discord.User, points: int):
        super().__init__(timeout=120)
        self.user = user
        self.points = points
        self.deposit_id = uuid.uuid4().hex[:8]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "⛔ الأمر ده مش ليك",
                ephemeral=True
            )
            return False
        return True

    async def _edit(self, interaction: discord.Interaction, text: str):
        await interaction.response.edit_message(
            content=text,
            view=None
        )

    @discord.ui.button(label="📱 Vodafone Cash", style=discord.ButtonStyle.success)
    async def vodafone(self, interaction: discord.Interaction, button: Button):
        await self._edit(
            interaction,
            f"""📄 **إثبات التحويل**
🆔 ID: `{self.deposit_id}`
💎 النقاط: **{self.points}**
💰 المبلغ: **{self.points}**
📱 الطريقة: **Vodafone Cash**

📞 حوّل على:
`{VODAFONE_NUMBER}`

📎 ابعت صورة إثبات التحويل **كرد عادي في الروم**"""
        )

    @discord.ui.button(label="💳 InstaPay", style=discord.ButtonStyle.primary)
    async def instapay(self, interaction: discord.Interaction, button: Button):
        await self._edit(
            interaction,
            f"""📄 **إثبات التحويل**
🆔 ID: `{self.deposit_id}`
💎 النقاط: **{self.points}**
💰 المبلغ: **{self.points}**
💳 الطريقة: **InstaPay**

📞 حوّل على:
`{INSTAPAY_NUMBER}`

📎 ابعت صورة إثبات التحويل **كرد عادي في الروم**"""
        )

    @discord.ui.button(label="🤖 ProBot Credit", style=discord.ButtonStyle.secondary)
    async def probot(self, interaction: discord.Interaction, button: Button):
        await self._edit(
            interaction,
            f"""📄 **إثبات التحويل**
🆔 ID: `{self.deposit_id}`
💎 النقاط: **{self.points}**
🤖 الطريقة: **ProBot Credit**

🆔 ProBot ID:
`{PROBOT_OWNER_ID}`

📎 ابعت إثبات التحويل **كرد عادي في الروم**"""
        )


# =========================
# Slash Command /deposit
# =========================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):

    if points <= 0:
        await interaction.response.send_message(
            "❌ عدد النقاط غير صحيح",
            ephemeral=True
        )
        return

    view = PaymentMethodView(interaction.user, points)

    await interaction.response.send_message(
        f"""💳 **شحن رصيد**
🆔 ID: `{view.deposit_id}`
💎 النقاط: **{points}**

اختر طريقة الدفع 👇""",
        view=view,
        ephemeral=True
    )


# =========================
# التقاط إثبات التحويل
# =========================
async def handle_proof_message(message: discord.Message):
    if message.author.bot:
        return

    if not message.attachments:
        return

    attachment = message.attachments[0]
    proof_url = attachment.url

    admin_channel = message.guild.get_channel(ADMIN_ACTION_CHANNEL_ID)
    if not admin_channel:
        return

    embed = discord.Embed(
        title="📥 طلب إيداع جديد",
        color=0xFFD700
    )
    embed.add_field(name="👤 المستخدم", value=message.author.mention, inline=False)
    embed.add_field(name="📎 رابط الإثبات", value=proof_url, inline=False)
    embed.set_image(url=proof_url)

    await admin_channel.send(embed=embed)

    try:
        await message.delete()
    except:
        pass

    await message.channel.send(
        "⏳ **في انتظار استلام الرصيد خلال 5 دقائق**",
        delete_after=10
    )
