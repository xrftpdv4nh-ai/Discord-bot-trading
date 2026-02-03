import discord
from discord import app_commands
from datetime import datetime

from config import (
    ADMIN_ACTION_CHANNEL_ID,
    LOG_CHANNEL_ID,
    VODAFONE_NUMBER,
    INSTAPAY_NUMBER,
    PROBOT_ID
)

# نخزن الطلبات مؤقتًا
PENDING_DEPOSITS = {}

# ================= SLASH COMMAND =================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    if points < 1000:
        await interaction.response.send_message(
            "⛔ الحد الأدنى للشحن **1000 نقطة**",
            ephemeral=True
        )
        return

    deposit_id = hex(int(datetime.now().timestamp()))[2:]
    amount = points  # 1 نقطة = 1 جنيه (تقدر تغيرها بعدين)

    PENDING_DEPOSITS[interaction.user.id] = {
        "id": deposit_id,
        "points": points,
        "amount": amount,
        "method": None
    }

    embed = discord.Embed(
        title="💳 شحن رصيد",
        description=(
            f"🆔 **ID:** `{deposit_id}`\n"
            f"💎 **النقاط:** `{points}`\n"
            f"💰 **المبلغ المطلوب:** `{amount}`\n\n"
            "**اختر طريقة الدفع:**"
        ),
        color=0x3498db
    )

    view = PaymentMethodView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ================= PAYMENT VIEW =================
class PaymentMethodView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="📱 فودافون كاش", style=discord.ButtonStyle.success)
    async def vodafone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_method(interaction, "Vodafone")

    @discord.ui.button(label="🏦 إنستا باي", style=discord.ButtonStyle.primary)
    async def instapay(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_method(interaction, "InstaPay")

    @discord.ui.button(label="🤖 ProBot", style=discord.ButtonStyle.secondary)
    async def probot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_method(interaction, "ProBot")

    async def select_method(self, interaction: discord.Interaction, method: str):
        data = PENDING_DEPOSITS.get(interaction.user.id)
        if not data:
            await interaction.response.send_message("⛔ الطلب غير موجود", ephemeral=True)
            return

        data["method"] = method

        if method == "Vodafone":
            target = VODAFONE_NUMBER
        elif method == "InstaPay":
            target = INSTAPAY_NUMBER
        else:
            target = str(PROBOT_ID)

        embed = discord.Embed(
            title="📎 إثبات التحويل",
            description=(
                f"🆔 **ID:** `{data['id']}`\n"
                f"💎 **النقاط:** `{data['points']}`\n"
                f"💰 **المبلغ:** `{data['amount']}`\n"
                f"💳 **الطريقة:** `{method}`\n\n"
                f"📤 **حوّل على:** `{target}`\n\n"
                "📎 **ابعت صورة إثبات التحويل كرسالة عادية في الروم**"
            ),
            color=0xf1c40f
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ================= PROOF HANDLER =================
async def handle_proof_message(message: discord.Message):
    if message.author.bot:
        return

    if not message.attachments:
        return

    user_id = message.author.id
    if user_id not in PENDING_DEPOSITS:
        return

    attachment = message.attachments[0]
    image_url = attachment.url
    data = PENDING_DEPOSITS[user_id]

    # احذف رسالة الصورة
    try:
        await message.delete()
    except:
        pass

    admin_channel = message.guild.get_channel(ADMIN_ACTION_CHANNEL_ID)
    log_channel = message.guild.get_channel(LOG_CHANNEL_ID)

    embed = discord.Embed(
        title="📥 طلب شحن جديد",
        description=(
            f"👤 **المستخدم:** {message.author.mention}\n"
            f"🆔 **ID:** `{data['id']}`\n"
            f"💎 **النقاط:** `{data['points']}`\n"
            f"💰 **المبلغ:** `{data['amount']}`\n"
            f"💳 **الطريقة:** `{data['method']}`\n\n"
            f"🖼️ **إثبات التحويل:** [اضغط هنا]({image_url})"
        ),
        color=0x2ecc71,
        timestamp=datetime.utcnow()
    )

    if admin_channel:
        await admin_channel.send(embed=embed)

    if log_channel:
        await log_channel.send(embed=embed)

    await message.channel.send(
        "⏳ **تم استلام إثبات التحويل**\n"
        "يرجى انتظار موافقة الإدارة خلال دقائق.",
        delete_after=10
    )

    del PENDING_DEPOSITS[user_id]
