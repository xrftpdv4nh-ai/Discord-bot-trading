import discord
from discord import app_commands
from discord.ui import View, Button
import uuid
import json
import os

# ================== CONFIG ==================
ADMIN_CHANNEL_ID = 1293008901142351952
DEPOSIT_FILE = "data/deposits.json"

os.makedirs("data", exist_ok=True)

# ================== JSON ==================
def load_json(path, default):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f)
        return default
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# ================== WALLET ==================
from admin.wallet_admin import add_balance

# ================== PAYMENT VIEW ==================
class PaymentView(View):
    def __init__(self, req_id: str):
        super().__init__(timeout=300)
        self.req_id = req_id

    async def choose(self, interaction: discord.Interaction, method: str):
        # الرد فورًا (مهم جدًا)
        await interaction.response.send_message(
            f"✅ اخترت **{method}**\n📎 ابعت صورة إثبات التحويل في نفس الشات",
            ephemeral=True
        )

        deposits = load_json(DEPOSIT_FILE, {})
        if self.req_id in deposits:
            deposits[self.req_id]["method"] = method
            save_json(DEPOSIT_FILE, deposits)

        # تعطيل الأزرار (من غير تعديل الرسالة)
        for b in self.children:
            b.disabled = True

    @discord.ui.button(label="Vodafone Cash", style=discord.ButtonStyle.primary, emoji="📱")
    async def vodafone(self, interaction: discord.Interaction, button: Button):
        await self.choose(interaction, "Vodafone Cash")

    @discord.ui.button(label="InstaPay", style=discord.ButtonStyle.success, emoji="💳")
    async def instapay(self, interaction: discord.Interaction, button: Button):
        await self.choose(interaction, "InstaPay")

    @discord.ui.button(label="ProBot", style=discord.ButtonStyle.secondary, emoji="🤖")
    async def probot(self, interaction: discord.Interaction, button: Button):
        await self.choose(interaction, "ProBot")

# ================== ADMIN VIEW ==================
class AdminDepositView(View):
    def __init__(self, req_id: str):
        super().__init__(timeout=None)
        self.req_id = req_id

    async def finalize(self, interaction: discord.Interaction, accept: bool):
        # الرد فورًا
        await interaction.response.send_message("⏳ جاري المعالجة...", ephemeral=True)

        deposits = load_json(DEPOSIT_FILE, {})
        if self.req_id not in deposits:
            return

        data = deposits[self.req_id]
        user = interaction.client.get_user(data["user_id"])

        if accept:
            add_balance(data["user_id"], data["points"])
            if user:
                try:
                    await user.send(
                        f"✅ **تم شحن رصيدك بنجاح**\n💎 النقاط: {data['points']}"
                    )
                except:
                    pass
        else:
            if user:
                try:
                    await user.send("❌ **تم رفض طلب الشحن**")
                except:
                    pass

        # قفل الطلب
        del deposits[self.req_id]
        save_json(DEPOSIT_FILE, deposits)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await self.finalize(interaction, True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await self.finalize(interaction, False)

# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    # الرد فورًا
    await interaction.response.send_message(
        "⏳ جاري إنشاء طلب الشحن...",
        ephemeral=True
    )

    req_id = uuid.uuid4().hex[:8]
    deposits = load_json(DEPOSIT_FILE, {})

    deposits[req_id] = {
        "user_id": interaction.user.id,
        "points": points,
        "method": None
    }
    save_json(DEPOSIT_FILE, deposits)

    embed = discord.Embed(
        title="💳 طلب شحن",
        description=f"💎 النقاط: **{points}**\nاختر طريقة الدفع:",
        color=0x3498db
    )
    embed.set_footer(text=f"ID: {req_id}")

    await interaction.followup.send(
        embed=embed,
        view=PaymentView(req_id),
        ephemeral=True
    )

# ================== PROOF HANDLER ==================
async def handle_proof_message(message: discord.Message):
    if not message.attachments:
        return

    deposits = load_json(DEPOSIT_FILE, {})

    for req_id, data in deposits.items():
        if data["user_id"] == message.author.id and data["method"]:
            admin_ch = message.guild.get_channel(ADMIN_CHANNEL_ID)
            if not admin_ch:
                return

            file = await message.attachments[0].to_file()

            embed = discord.Embed(
                title="📥 طلب إيداع جديد",
                color=0xf1c40f
            )
            embed.add_field(name="👤 المستخدم", value=message.author.mention, inline=False)
            embed.add_field(name="💎 النقاط", value=str(data["points"]), inline=True)
            embed.add_field(name="💳 الطريقة", value=data["method"], inline=True)
            embed.set_footer(text=f"ID: {req_id}")

            await admin_ch.send(
                embed=embed,
                file=file,
                view=AdminDepositView(req_id)
            )

            await message.channel.send(
                "⏳ **تم استلام إثبات التحويل**\nطلبك تحت المراجعة ✅",
                delete_after=15
            )
            return
