import discord
from discord import app_commands
from discord.ui import View, Button
import uuid

# ========= CONFIG =========
ADMIN_CHANNEL_ID = 1293008901142351952  # روم القبول / الرفض
VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"
PROBOT_ID = "802148738939748373"

# ========= MEMORY =========
pending_requests = {}   # user_id -> data
awaiting_proof = {}     # user_id -> request_id


# ========= PAYMENT VIEW =========
class PaymentMethodView(View):
    def __init__(self, user: discord.Member, amount: int):
        super().__init__(timeout=300)
        self.user = user
        self.amount = amount
        self.request_id = str(uuid.uuid4())[:8]

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def _select(self, interaction, method, target):
        pending_requests[self.user.id] = {
            "id": self.request_id,
            "user": self.user,
            "amount": self.amount,
            "method": method,
            "target": target
        }
        awaiting_proof[self.user.id] = self.request_id

        await interaction.response.send_message(
            f"📎 **ابعت صورة إثبات التحويل هنا**\n\n"
            f"🆔 ID: `{self.request_id}`\n"
            f"💰 المبلغ: `{self.amount}`\n"
            f"💳 الطريقة: `{method}`\n"
            f"➡️ حوّل على: `{target}`",
            ephemeral=False
        )
        self.stop()

    @discord.ui.button(label="Vodafone Cash", style=discord.ButtonStyle.primary)
    async def vodafone(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "Vodafone Cash", VODAFONE_NUMBER)

    @discord.ui.button(label="InstaPay", style=discord.ButtonStyle.success)
    async def instapay(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "InstaPay", INSTAPAY_NUMBER)

    @discord.ui.button(label="ProBot Credit", style=discord.ButtonStyle.secondary)
    async def probot(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "ProBot Credit", PROBOT_ID)


# ========= ADMIN VIEW =========
class AdminDecisionView(View):
    def __init__(self, request_id: str, user: discord.Member, amount: int):
        super().__init__(timeout=None)
        self.request_id = request_id
        self.user = user
        self.amount = amount

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            f"✅ تم قبول الإيداع `{self.request_id}`",
            ephemeral=True
        )
        self.stop()

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            f"❌ تم رفض الإيداع `{self.request_id}`",
            ephemeral=True
        )
        self.stop()


# ========= SLASH COMMAND =========
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(amount="عدد النقاط")
async def deposit(interaction: discord.Interaction, amount: int):
    if amount < 1000:
        await interaction.response.send_message(
            "❌ الحد الأدنى للشحن 1000 نقطة",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="💰 شحن رصيد",
        description=f"عدد النقاط: `{amount}`\nاختر طريقة الدفع 👇",
        color=0x3498db
    )

    await interaction.response.send_message(
        embed=embed,
        view=PaymentMethodView(interaction.user, amount)
    )


# ========= PROOF HANDLER =========
async def handle_proof_message(message: discord.Message):
    if message.author.id not in awaiting_proof:
        return

    if not message.attachments:
        return

    request_id = awaiting_proof.pop(message.author.id)
    data = pending_requests.pop(message.author.id, None)

    if not data:
        return

    # حذف صورة المستخدم
    try:
        await message.delete()
    except:
        pass

    admin_channel = message.guild.get_channel(ADMIN_CHANNEL_ID)
    if not admin_channel:
        return

    embed = discord.Embed(
        title="📥 طلب إيداع جديد",
        color=0xf1c40f
    )
    embed.add_field(name="المستخدم", value=data["user"].mention, inline=False)
    embed.add_field(name="ID", value=f"`{request_id}`", inline=False)
    embed.add_field(name="المبلغ", value=str(data["amount"]), inline=True)
    embed.add_field(name="الطريقة", value=data["method"], inline=True)

    embed.set_image(url=message.attachments[0].url)

    await admin_channel.send(
        embed=embed,
        view=AdminDecisionView(request_id, data["user"], data["amount"])
    )
