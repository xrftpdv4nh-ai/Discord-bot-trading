import discord
from discord import app_commands
from discord.ui import View, Button
import json
import os
import uuid

# ================== SETTINGS ==================
ADMIN_ACTION_CHANNEL_ID = 1293008901142351952
LOG_CHANNEL_ID = 1293146723417587763

VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"
PROBOT_ID = "802148738939748373"

PRICE_PER_1000 = 10  # 1000 نقطة = 10 جنيه
PROBOT_FEE_RATE = 0.053  # 5.3%

DATA_FILE = "data/deposits.json"

# ================== HELPERS ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ================== PAYMENT VIEW ==================
class PaymentView(View):
    def __init__(self, req_id: str):
        super().__init__(timeout=300)
        self.req_id = req_id

    async def disable(self, interaction):
        for c in self.children:
            c.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="📱 Vodafone Cash", style=discord.ButtonStyle.primary)
async def vodafone(self, interaction: discord.Interaction, button: Button):
    await interaction.response.defer(ephemeral=True)
    await self.select_method(interaction, "Vodafone")

    @discord.ui.button(label="💳 InstaPay", style=discord.ButtonStyle.success)
async def instapay(self, interaction: discord.Interaction, button: Button):
    await interaction.response.defer(ephemeral=True)
    await self.select_method(interaction, "InstaPay")

@discord.ui.button(label="🤖 ProBot", style=discord.ButtonStyle.secondary)
async def probot(self, interaction: discord.Interaction, button: Button):
    await interaction.response.defer(ephemeral=True)
    await self.select_method(interaction, "ProBot")

    async def select_method(self, interaction, method):
        data = load_data()
        if self.req_id not in data:
            await interaction.response.send_message("❌ الطلب غير موجود", ephemeral=True)
            return

        req = data[self.req_id]
        if req["status"] != "waiting_method":
            await interaction.response.send_message("⛔ تم اختيار طريقة دفع بالفعل", ephemeral=True)
            return

        points = req["points"]
        amount = (points / 1000) * PRICE_PER_1000

        if method == "ProBot":
            amount = round(amount * (1 + PROBOT_FEE_RATE))

        req["method"] = method
        req["amount"] = int(amount)
        req["status"] = "waiting_proof"
        save_data(data)

        await self.disable(interaction)

        await interaction.response.send_message(
            f"💰 **المبلغ المطلوب:** `{req['amount']}` جنيه\n"
            f"📌 **طريقة الدفع:** `{method}`\n\n"
            f"📨 **أرسل صورة إثبات التحويل في نفس الروم برسالة عادية**",
            ephemeral=True
        )

# ================== ADMIN VIEW ==================
class AdminView(View):
    def __init__(self, req_id: str):
        super().__init__(timeout=None)
        self.req_id = req_id

    async def lock(self, interaction):
        for c in self.children:
            c.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        data = load_data()
        req = data.get(self.req_id)
        if not req or req["status"] != "under_review":
            await interaction.response.send_message("❌ الطلب غير صالح", ephemeral=True)
            return

        req["status"] = "approved"
        save_data(data)

        user = interaction.guild.get_member(req["user_id"])
        if user:
            try:
                await user.send(
                    f"✅ **تم قبول طلب الشحن**\n"
                    f"💎 النقاط: `{req['points']}`"
                )
            except:
                pass

        await self.lock(interaction)
        await interaction.response.send_message("✅ تم القبول", ephemeral=True)

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        data = load_data()
        req = data.get(self.req_id)
        if not req or req["status"] != "under_review":
            await interaction.response.send_message("❌ الطلب غير صالح", ephemeral=True)
            return

        req["status"] = "rejected"
        save_data(data)

        user = interaction.guild.get_member(req["user_id"])
        if user:
            try:
                await user.send("❌ تم رفض طلب الشحن")
            except:
                pass

        await self.lock(interaction)
        await interaction.response.send_message("❌ تم الرفض", ephemeral=True)

# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    if points < 1000:
        await interaction.response.send_message("❌ أقل شحن 1000 نقطة", ephemeral=True)
        return

    req_id = uuid.uuid4().hex[:8]

    data = load_data()
    data[req_id] = {
        "user_id": interaction.user.id,
        "points": points,
        "status": "waiting_method"
    }
    save_data(data)

    embed = discord.Embed(
        title="💳 شحن رصيد",
        description=f"💎 النقاط: `{points}`\nاختر طريقة الدفع:",
        color=0x3498db
    )
    embed.set_footer(text=f"ID: {req_id}")

    await interaction.response.send_message(
        embed=embed,
        view=PaymentView(req_id),
        ephemeral=True
    )

# ================== PROOF HANDLER ==================
async def handle_proof_message(message: discord.Message):
    if not message.attachments:
        return

    data = load_data()

    for req_id, req in data.items():
        if req["user_id"] == message.author.id and req["status"] == "waiting_proof":
            req["status"] = "under_review"
            save_data(data)

            try:
                await message.delete()
            except:
                pass

            await message.channel.send(
                "⏳ **تم استلام إثبات التحويل**\n"
                "طلبك الآن **تحت المراجعة** وسيتم الرد عليك قريبًا ✅",
                delete_after=15
            )

            admin_ch = message.guild.get_channel(ADMIN_ACTION_CHANNEL_ID)
            if not admin_ch:
                return

            embed = discord.Embed(
                title="📥 طلب إيداع جديد",
                color=0xf1c40f
            )
            embed.add_field(name="👤 المستخدم", value=message.author.mention, inline=False)
            embed.add_field(name="💎 النقاط", value=req["points"], inline=True)
            embed.add_field(name="💰 المبلغ", value=req["amount"], inline=True)
            embed.add_field(name="💳 الطريقة", value=req["method"], inline=False)
            embed.set_footer(text=f"ID: {req_id}")
            embed.set_image(url=message.attachments[0].url)

            await admin_ch.send(embed=embed, view=AdminView(req_id))
            return
