import discord
from discord import app_commands
from discord.ui import View, Button
import json
import uuid
import os

# ================== SAFE CONFIG ==================
# لو أي متغير مش موجود في config.py مش هيعمل كراش
try:
    from config import (
        ADMIN_ACTION_CHANNEL_ID,
        LOG_CHANNEL_ID,
        VODAFONE_NUMBER,
        INSTAPAY_NUMBER,
        PROBOT_ID
    )
except ImportError:
    ADMIN_ACTION_CHANNEL_ID = 1293008901142351952
    LOG_CHANNEL_ID = 1293146723417587763
    VODAFONE_NUMBER = "01009137618"
    INSTAPAY_NUMBER = "01124808116"
    PROBOT_ID = 802148738939748373

DATA_FILE = "data/deposits.json"

# ================== FILE UTILS ==================
def load_deposits():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_deposits(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ================== ADMIN VIEW ==================
class AdminDepositView(View):
    def __init__(self, deposit_id: str):
        super().__init__(timeout=None)
        self.deposit_id = deposit_id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        data = load_deposits()
        dep = data.get(self.deposit_id)
        if not dep:
            await interaction.response.send_message("❌ الطلب غير موجود", ephemeral=True)
            return

        dep["status"] = "confirmed"
        save_deposits(data)

        await interaction.response.send_message("✅ تم قبول الإيداع", ephemeral=True)

        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(
                f"✅ **تم قبول إيداع**\n"
                f"👤 <@{dep['user_id']}>\n"
                f"💰 `{dep['amount']}`\n"
                f"💎 `{dep['points']}`"
            )

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        data = load_deposits()
        dep = data.get(self.deposit_id)
        if not dep:
            await interaction.response.send_message("❌ الطلب غير موجود", ephemeral=True)
            return

        dep["status"] = "rejected"
        save_deposits(data)

        await interaction.response.send_message("❌ تم رفض الإيداع", ephemeral=True)

# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    amount = points  # 1 نقطة = 1 جنيه (تقدر تغيرها)

    deposit_id = uuid.uuid4().hex[:8]

    data = load_deposits()
    data[str(interaction.user.id)] = {
        "id": deposit_id,
        "user_id": interaction.user.id,
        "points": points,
        "amount": amount,
        "method": None,
        "status": "waiting"
    }
    save_deposits(data)

    embed = discord.Embed(
        title="💳 شحن رصيد",
        description=(
            f"🆔 ID: `{deposit_id}`\n"
            f"💎 النقاط: `{points}`\n"
            f"💰 المبلغ: `{amount}`\n\n"
            "اختر طريقة التحويل:"
        ),
        color=0x3498db
    )

    view = View()
    view.add_item(Button(label="Vodafone Cash", style=discord.ButtonStyle.primary, custom_id="vodafone"))
    view.add_item(Button(label="InstaPay", style=discord.ButtonStyle.primary, custom_id="instapay"))
    view.add_item(Button(label="ProBot Credit", style=discord.ButtonStyle.secondary, custom_id="probot"))

    await interaction.response.send_message(embed=embed, view=view)

# ================== BUTTON HANDLER ==================
async def handle_payment_method(interaction: discord.Interaction):
    data = load_deposits()
    dep = data.get(str(interaction.user.id))
    if not dep:
        await interaction.response.send_message("❌ لا يوجد طلب", ephemeral=True)
        return

    method = interaction.data["custom_id"]
    dep["method"] = method
    save_deposits(data)

    if method == "vodafone":
        txt = f"📱 حول على فودافون كاش:\n`{VODAFONE_NUMBER}`"
    elif method == "instapay":
        txt = f"🏦 حول على إنستا باي:\n`{INSTAPAY_NUMBER}`"
    else:
        txt = f"🤖 حول ProBot Credit إلى:\n`{PROBOT_ID}`"

    await interaction.response.send_message(
        f"{txt}\n\n"
        "📎 **ابعت صورة إثبات التحويل كرسالة عادية في الروم**",
    )

# ================== IMAGE LISTENER ==================
async def handle_proof_message(message: discord.Message):
    if not message.attachments:
        return

    data = load_deposits()
    user_key = str(message.author.id)

    if user_key not in data:
        return

    dep = data[user_key]
    if dep["status"] != "waiting":
        return

    image_url = message.attachments[0].url
    admin_channel = message.guild.get_channel(ADMIN_ACTION_CHANNEL_ID)

    embed = discord.Embed(
        title="🧾 طلب إيداع جديد",
        description=(
            f"👤 {message.author.mention}\n"
            f"💰 `{dep['amount']}`\n"
            f"💎 `{dep['points']}`\n"
            f"💳 `{dep['method']}`\n"
            f"🆔 `{dep['id']}`"
        ),
        color=0xf1c40f
    )
    embed.set_image(url=image_url)

    await admin_channel.send(embed=embed, view=AdminDepositView(dep["id"]))

    await message.delete()
    await message.channel.send(
        "⏳ **تم استلام إثبات التحويل**\nيرجى الانتظار حتى مراجعة الإدارة",
        delete_after=20
    )
