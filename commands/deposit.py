import discord
from discord import app_commands
from discord.ui import View, Button
import uuid
import json
import os
import math

# ================== CONFIG ==================
ADMIN_CHANNEL_ID = 1293008901142351952
LOG_CHANNEL_ID = 1293146723417587763

VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"
PROBOT_ID = "802148738939748373"

PRICE_PER_1000_EGP = 10
PROBOT_TAX_RATE = 0.053  # 5.3%

DEPOSIT_FILE = "data/deposits.json"
WALLET_FILE = "data/wallets.json"

# ================== UTILS ==================
def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ================== PAYMENT VIEW ==================
class PaymentMethodView(View):
    def __init__(self, request_id, points, user):
        super().__init__(timeout=300)
        self.request_id = request_id
        self.points = points
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def send_price(self, interaction, method, target, price_text):
        deposits = load_json(DEPOSIT_FILE, {})
        deposits[self.request_id]["method"] = method
        deposits[self.request_id]["status"] = "waiting_proof"
        save_json(DEPOSIT_FILE, deposits)

        embed = discord.Embed(
            title="📎 إثبات التحويل",
            color=0xf39c12,
            description=(
                f"🆔 **ID:** `{self.request_id}`\n"
                f"💎 **النقاط:** `{self.points}`\n"
                f"{price_text}\n"
                f"➡️ **حوّل على:** `{target}`\n\n"
                "📸 ابعت صورة إثبات التحويل **كرسالة عادية في نفس الروم**"
            )
        )

        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="📱 Vodafone Cash", style=discord.ButtonStyle.success)
    async def vodafone(self, interaction: discord.Interaction, button: Button):
        egp = (self.points / 1000) * PRICE_PER_1000_EGP
        price_text = f"💰 **المبلغ المطلوب:** `{int(egp)} جنيه`"
        await self.send_price(interaction, "Vodafone Cash", VODAFONE_NUMBER, price_text)

    @discord.ui.button(label="🏦 InstaPay", style=discord.ButtonStyle.primary)
    async def instapay(self, interaction: discord.Interaction, button: Button):
        egp = (self.points / 1000) * PRICE_PER_1000_EGP
        price_text = f"💰 **المبلغ المطلوب:** `{int(egp)} جنيه`"
        await self.send_price(interaction, "InstaPay", INSTAPAY_NUMBER, price_text)

    @discord.ui.button(label="🤖 ProBot Credit", style=discord.ButtonStyle.secondary)
    async def probot(self, interaction: discord.Interaction, button: Button):
        base = self.points
        tax = math.ceil(base * PROBOT_TAX_RATE)
        total = base + tax
        price_text = (
            f"🤖 **السعر الأساسي:** `{base}`\n"
            f"📈 **ضريبة التحويل:** `{tax}`\n"
            f"💰 **الإجمالي المطلوب:** `{total} ProBot Credit`"
        )
        await self.send_price(interaction, "ProBot", PROBOT_ID, price_text)

# ================== ADMIN VIEW ==================
class AdminDecisionView(View):
    def __init__(self, request_id):
        super().__init__(timeout=None)
        self.request_id = request_id

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.success,
        custom_id="deposit_confirm"
    )
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await self.handle(interaction, approved=True)

    @discord.ui.button(
        label="Reject",
        style=discord.ButtonStyle.danger,
        custom_id="deposit_reject"
    )
    async def reject(self, interaction: discord.Interaction, button: Button):
        await self.handle(interaction, approved=False)

    async def handle(self, interaction: discord.Interaction, approved: bool):
        deposits = load_json(DEPOSIT_FILE, {})
        wallets = load_json(WALLET_FILE, {})

        if self.request_id not in deposits:
            await interaction.response.send_message(
                "❌ الطلب ده غير موجود أو اتنفذ قبل كده",
                ephemeral=True
            )
            return

        data = deposits[self.request_id]
        if data.get("status") not in ["waiting_review", "waiting_proof"]:
            await interaction.response.send_message(
                "⚠️ الطلب ده اتراجع بالفعل",
                ephemeral=True
            )
            return

        user = interaction.guild.get_member(int(data["user_id"]))

        if approved:
            wallets.setdefault(str(user.id), {"balance": 0})
            wallets[str(user.id)]["balance"] += data["points"]
            data["status"] = "approved"

            try:
                await user.send(
                    f"✅ تم شحن **{data['points']} نقطة** بنجاح"
                )
            except:
                pass

        else:
            data["status"] = "rejected"
            try:
                await user.send("❌ تم رفض طلب الشحن")
            except:
                pass

        save_json(WALLET_FILE, wallets)
        save_json(DEPOSIT_FILE, deposits)

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(view=self)

# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    if points < 1000:
        await interaction.response.send_message(
            "⛔ الحد الأدنى للشحن **1000 نقطة**",
            ephemeral=True
        )
        return

    request_id = uuid.uuid4().hex[:8]

    deposits = load_json(DEPOSIT_FILE, {})
    deposits[request_id] = {
        "user_id": interaction.user.id,
        "points": points,
        "status": "waiting_method"
    }
    save_json(DEPOSIT_FILE, deposits)

    embed = discord.Embed(
        title="💳 اختر طريقة الدفع",
        description=f"💎 **عدد النقاط:** `{points}`",
        color=0x3498db
    )
    embed.set_footer(text=f"ID: {request_id}")

    await interaction.response.send_message(
        embed=embed,
        view=PaymentMethodView(request_id, points, interaction.user),
        ephemeral=True
    )

# ================== PROOF HANDLER ==================
async def handle_proof_message(message: discord.Message):
    if not message.attachments:
        return

    deposits = load_json(DEPOSIT_FILE, {})

    for req_id, data in deposits.items():
        if data["user_id"] == message.author.id and data["status"] == "waiting_proof":

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
            embed.add_field(name="👤 المستخدم", value=message.author.mention, inline=False)
            embed.add_field(name="💎 النقاط", value=str(data["points"]), inline=True)
            embed.add_field(name="💳 الطريقة", value=data["method"], inline=True)
            embed.set_footer(text=f"ID: {req_id}")
            embed.set_image(url=f"attachment://{file.filename}")

            await admin_channel.send(
                embed=embed,
                file=file,
                view=AdminDecisionView(req_id)
            )
            break
