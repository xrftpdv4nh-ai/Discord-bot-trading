import discord
from discord import app_commands
from discord.ui import View, Button
import json
import uuid
import os

# ================== إعدادات ==================
ADMIN_CHANNEL_ID = 1293008901142351952
DEPOSIT_FILE = "data/deposits.json"
WALLETS_FILE = "data/wallets.json"

# ================== JSON ==================
def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ================== Wallet ==================
def add_balance(user_id: int, amount: int):
    wallets = load_json(WALLETS_FILE, {})
    uid = str(user_id)
    wallets[uid] = wallets.get(uid, 0) + amount
    save_json(WALLETS_FILE, wallets)

# ================== View ==================
class DepositView(View):
    def __init__(self, req_id: str):
        super().__init__(timeout=None)
        self.req_id = req_id

    async def _finalize(self, interaction: discord.Interaction, accepted: bool):
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
                        f"✅ **تم شحن رصيدك بنجاح**\n"
                        f"💎 النقاط: {data['points']}"
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
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await self._finalize(interaction, True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await self._finalize(interaction, False)

# ================== Slash Command ==================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    await interaction.response.defer(ephemeral=True)

    req_id = uuid.uuid4().hex[:8]

    deposits = load_json(DEPOSIT_FILE, {})
    deposits[req_id] = {
        "user_id": interaction.user.id,
        "points": points
    }
    save_json(DEPOSIT_FILE, deposits)

    embed = discord.Embed(
        title="💳 شحن رصيد",
        color=0x2f3136
    )
    embed.add_field(name="💎 النقاط", value=str(points), inline=False)
    embed.set_footer(text=f"ID: {req_id}")

    await interaction.followup.send(
        embed=embed,
        view=PaymentView(req_id),
        ephemeral=True
    )

# ================== اختيار طريقة الدفع ==================
class PaymentView(View):
    def __init__(self, req_id):
        super().__init__(timeout=120)
        self.req_id = req_id

    async def handle(self, interaction, method):
        deposits = load_json(DEPOSIT_FILE, {})
        if self.req_id not in deposits:
            await interaction.response.send_message("❌ الطلب غير موجود", ephemeral=True)
            return

        deposits[self.req_id]["method"] = method
        save_json(DEPOSIT_FILE, deposits)

        await interaction.response.send_message(
            "📎 **ابعت صورة إثبات التحويل في نفس الروم**",
            ephemeral=True
        )

        self.stop()

    @discord.ui.button(label="Vodafone Cash", style=discord.ButtonStyle.primary)
    async def vodafone(self, interaction, button):
        await self.handle(interaction, "Vodafone")

    @discord.ui.button(label="InstaPay", style=discord.ButtonStyle.success)
    async def instapay(self, interaction, button):
        await self.handle(interaction, "InstaPay")

    @discord.ui.button(label="ProBot", style=discord.ButtonStyle.secondary)
    async def probot(self, interaction, button):
        await self.handle(interaction, "ProBot")

# ================== Proof Handler ==================
async def handle_proof_message(message: discord.Message):
    if not message.attachments:
        return

    deposits = load_json(DEPOSIT_FILE, {})

    for req_id, data in deposits.items():
        if data["user_id"] == message.author.id and "method" in data:
            admin_channel = message.guild.get_channel(ADMIN_CHANNEL_ID)
            if not admin_channel:
                return

            embed = discord.Embed(
                title="📥 طلب إيداع جديد",
                color=0xf1c40f
            )
            embed.add_field(name="👤 المستخدم", value=message.author.mention, inline=False)
            embed.add_field(name="💎 النقاط", value=data["points"], inline=False)
            embed.add_field(name="💳 الطريقة", value=data["method"], inline=False)
            embed.set_footer(text=f"ID: {req_id}")

            file = await message.attachments[0].to_file()

            await admin_channel.send(
                embed=embed,
                file=file,
                view=DepositView(req_id)
            )

            try:
                await message.delete()
            except:
                pass

            await message.channel.send(
                "⏳ **تم استلام إثبات التحويل – الطلب تحت المراجعة**",
                delete_after=10
            )
            return
