import discord
from discord import app_commands
from discord.ext import commands
import uuid
import json
import os

# ================== FILES ==================
DEPOSIT_FILE = "data/deposits.json"
WALLET_FILE = "data/wallets.json"
ADMIN_CHANNEL_ID = 1293008901142351952

os.makedirs("data", exist_ok=True)

# ================== JSON UTILS ==================
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
def add_balance(user_id: int, amount: int):
    wallets = load_json(WALLET_FILE, {})
    uid = str(user_id)
    wallets[uid] = wallets.get(uid, 0) + amount
    save_json(WALLET_FILE, wallets)

# ================== PAYMENT VIEW ==================
class PaymentView(discord.ui.View):
    def __init__(self, req_id: str):
        super().__init__(timeout=300)
        self.req_id = req_id

    async def select_method(self, interaction: discord.Interaction, method: str):
        await interaction.response.defer(ephemeral=True)

        deposits = load_json(DEPOSIT_FILE, {})
        if self.req_id not in deposits:
            await interaction.followup.send("❌ الطلب غير موجود", ephemeral=True)
            return

        deposits[self.req_id]["method"] = method
        save_json(DEPOSIT_FILE, deposits)

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(view=self)
        await interaction.followup.send(
            f"✅ تم اختيار طريقة الدفع **{method}**\n📎 ابعت صورة إثبات التحويل في نفس الشات",
            ephemeral=True
        )

    @discord.ui.button(label="Vodafone Cash", style=discord.ButtonStyle.primary, emoji="📱")
    async def vodafone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_method(interaction, "Vodafone Cash")

    @discord.ui.button(label="InstaPay", style=discord.ButtonStyle.success, emoji="💳")
    async def instapay(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_method(interaction, "InstaPay")

    @discord.ui.button(label="ProBot", style=discord.ButtonStyle.secondary, emoji="🤖")
    async def probot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select_method(interaction, "ProBot")

# ================== ADMIN VIEW ==================
class DepositAdminView(discord.ui.View):
    def __init__(self, req_id: str):
        super().__init__(timeout=None)
        self.req_id = req_id

    async def finalize(self, interaction: discord.Interaction, accepted: bool):
        await interaction.response.defer(ephemeral=True)

        deposits = load_json(DEPOSIT_FILE, {})
        if self.req_id not in deposits:
            await interaction.followup.send("❌ الطلب غير موجود", ephemeral=True)
            return

        data = deposits[self.req_id]
        user = interaction.client.get_user(data["user_id"])

        if accepted:
            add_balance(data["user_id"], data["points"])
            if user:
                try:
                    await user.send(
                        f"✅ **تم شحن رصيدك بنجاح**\n💎 النقاط: {data['points']}"
                    )
                except:
                    pass
            result = "✅ تم قبول الطلب وشحن الرصيد"
        else:
            if user:
                try:
                    await user.send("❌ **تم رفض طلب الشحن**")
                except:
                    pass
            result = "🚫 تم رفض الطلب"

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(view=self)

        del deposits[self.req_id]
        save_json(DEPOSIT_FILE, deposits)

        await interaction.followup.send(result, ephemeral=True)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.finalize(interaction, True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.finalize(interaction, False)

# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    await interaction.response.defer(ephemeral=True)

    req_id = uuid.uuid4().hex[:8]
    deposits = load_json(DEPOSIT_FILE, {})

    deposits[req_id] = {
        "user_id": interaction.user.id,
        "points": points,
        "method": None
    }
    save_json(DEPOSIT_FILE, deposits)

    embed = discord.Embed(
        title="💳 شحن رصيد",
        color=0x3498db
    )
    embed.add_field(name="💎 النقاط", value=str(points), inline=False)
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
                view=DepositAdminView(req_id)
            )

            await message.channel.send(
                "⏳ تم استلام إثبات التحويل، طلبك تحت المراجعة ✅",
                delete_after=15
            )
            return
