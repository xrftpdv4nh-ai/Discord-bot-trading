import discord
from discord import app_commands
from discord.ui import View, Button
import uuid

# ================== CONFIG ==================
ADMIN_CHANNEL_ID = 1293008901142351952   # روم القبول / الرفض
LOG_CHANNEL_ID = 1293146723417587763     # روم اللوج

VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"
PROBOT_ID = "802148738939748373"

# ================== TEMP STORAGE ==================
awaiting_proof = {}     # user_id -> request_id
pending_requests = {}   # user_id -> data

# ================== ADMIN VIEW ==================
class AdminDecisionView(View):
    def __init__(self, request_id, user, amount):
        super().__init__(timeout=None)
        self.request_id = request_id
        self.user = user
        self.amount = amount

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            f"✅ **تم قبول الإيداع**\n👤 {self.user.mention}\n💰 `{self.amount}`",
            ephemeral=True
        )

        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(
                f"✅ **إيداع مقبول**\n"
                f"👤 {self.user.mention}\n"
                f"💰 `{self.amount}`\n"
                f"🆔 `{self.request_id}`"
            )

        self.disable_all_items()
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            f"❌ **تم رفض الإيداع**\n👤 {self.user.mention}",
            ephemeral=True
        )

        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(
                f"❌ **إيداع مرفوض**\n"
                f"👤 {self.user.mention}\n"
                f"🆔 `{self.request_id}`"
            )

        self.disable_all_items()
        await interaction.message.edit(view=self)

# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(amount="عدد النقاط")
async def deposit(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message(
            "⛔ **رقم غير صحيح**",
            ephemeral=True
        )
        return

    request_id = uuid.uuid4().hex[:8]

    pending_requests[interaction.user.id] = {
        "user": interaction.user,
        "amount": amount
    }
    awaiting_proof[interaction.user.id] = request_id

    embed = discord.Embed(
        title="💳 شحن رصيد",
        color=0x3498db
    )
    embed.add_field(name="🆔 ID", value=request_id, inline=False)
    embed.add_field(name="💎 النقاط", value=str(amount), inline=True)
    embed.add_field(name="💰 المبلغ", value=str(amount), inline=True)

    embed.add_field(
        name="طرق الدفع",
        value=(
            f"📱 **Vodafone Cash:** `{VODAFONE_NUMBER}`\n"
            f"🏦 **InstaPay:** `{INSTAPAY_NUMBER}`\n"
            f"🤖 **ProBot Credit:** `{PROBOT_ID}`"
        ),
        inline=False
    )

    embed.set_footer(text="📎 ابعت صورة إثبات التحويل كرسالة عادية في نفس الروم")

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )

# ================== PROOF HANDLER ==================
async def handle_proof_message(message: discord.Message):
    if message.author.id not in awaiting_proof:
        return

    if not message.attachments:
        return

    request_id = awaiting_proof.pop(message.author.id)
    data = pending_requests.pop(message.author.id, None)
    if not data:
        return

    attachment = message.attachments[0]
    file = await attachment.to_file()

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
    embed.add_field(name="👤 المستخدم", value=data["user"].mention, inline=False)
    embed.add_field(name="💰 المبلغ", value=str(data["amount"]), inline=True)
    embed.add_field(name="🆔 ID", value=request_id, inline=True)

    embed.set_image(url=f"attachment://{file.filename}")

    await admin_channel.send(
        embed=embed,
        file=file,
        view=AdminDecisionView(request_id, data["user"], data["amount"])
    )
