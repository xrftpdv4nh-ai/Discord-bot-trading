import discord
from discord import app_commands
from discord.ui import View, Button
import uuid
import json
import os

from config import (
    ADMIN_CHANNEL_ID,
    VODAFONE_NUMBER,
    INSTAPAY_NUMBER,
    PROBOT_ID
)

# ================== FILES ==================
DEPOSIT_FILE = "data/deposits.json"
WALLET_FILE = "data/wallets.json"

os.makedirs("data", exist_ok=True)

# ================== HELPERS ==================
def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_balance(user_id: int, amount: int):
    wallets = load_json(WALLET_FILE, {})
    uid = str(user_id)
    wallets[uid] = wallets.get(uid, 0) + amount
    save_json(WALLET_FILE, wallets)

# ================== PAYMENT VIEW ==================
class PaymentView(View):
    def __init__(self, points, req_id):
        super().__init__(timeout=300)
        self.points = points
        self.req_id = req_id

    async def _select(self, interaction: discord.Interaction, method: str):
        await interaction.response.defer(ephemeral=True)

        deposits = load_json(DEPOSIT_FILE, {})
        if self.req_id not in deposits:
            return

        deposits[self.req_id]["method"] = method
        deposits[self.req_id]["status"] = "waiting_proof"
        save_json(DEPOSIT_FILE, deposits)

        amount_egp = self.points / 100

        if method == "Vodafone Cash":
            text = f"📱 حول **{amount_egp:.2f} جنيه** على:\n`{VODAFONE_NUMBER}`"
        elif method == "InstaPay":
            text = f"💳 حول **{amount_egp:.2f} جنيه** على:\n`{INSTAPAY_NUMBER}`"
        else:
            text = f"🤖 ابعت **{self.points} نقطة** إلى:\n`{PROBOT_ID}`"

        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            content=f"{text}\n\n📎 **ابعت صورة إثبات التحويل هنا**",
            view=None
        )

    @discord.ui.button(label="Vodafone Cash", style=discord.ButtonStyle.primary)
    async def vodafone(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "Vodafone Cash")

    @discord.ui.button(label="InstaPay", style=discord.ButtonStyle.success)
    async def instapay(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "InstaPay")

    @discord.ui.button(label="ProBot", style=discord.ButtonStyle.secondary)
    async def probot(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "ProBot")

# ================== ADMIN VIEW ==================
class AdminView(View):
    def __init__(self, req_id):
        super().__init__(timeout=None)
        self.req_id = req_id

    async def _finalize(self, interaction: discord.Interaction, accepted: bool):
        await interaction.response.defer(ephemeral=True)

        deposits = load_json(DEPOSIT_FILE, {})
        if self.req_id not in deposits:
            await interaction.followup.send("❌ الطلب غير موجود")
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

        for c in self.children:
            c.disabled = True

        await interaction.message.edit(view=self)

        del deposits[self.req_id]
        save_json(DEPOSIT_FILE, deposits)

        await interaction.followup.send(result)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await self._finalize(interaction, True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await self._finalize(interaction, False)

# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    req_id = uuid.uuid4().hex[:8]

    deposits = load_json(DEPOSIT_FILE, {})
    deposits[req_id] = {
        "user_id": interaction.user.id,
        "points": points,
        "method": None,
        "status": "choose_method"
    }
    save_json(DEPOSIT_FILE, deposits)

    embed = discord.Embed(
        title="💳 شحن رصيد",
        description=(
            f"💎 النقاط: **{points}**\n"
            f"💰 المبلغ: **{points / 100:.2f} جنيه**\n\n"
            "اختر طريقة الدفع:"
        ),
        color=0x2ecc71
    )
    embed.set_footer(text=f"ID: {req_id}")

    await interaction.response.send_message(
        embed=embed,
        view=PaymentView(points, req_id),
        ephemeral=True
    )

# ================== PROOF HANDLER ==================
async def handle_proof_message(message: discord.Message):
    if not message.attachments or message.author.bot:
        return

    deposits = load_json(DEPOSIT_FILE, {})

    for req_id, data in deposits.items():
        if (
            data["user_id"] == message.author.id
            and data.get("status") == "waiting_proof"
        ):
            file = await message.attachments[0].to_file()

            try:
                await message.delete()
            except:
                pass

            await message.channel.send(
                "⏳ **تم استلام إثبات التحويل**\nطلبك تحت المراجعة ✅",
                delete_after=10
            )

            ch = message.guild.get_channel(ADMIN_CHANNEL_ID)
            if not ch:
                return

            embed = discord.Embed(
                title="📥 طلب إيداع جديد",
                color=0xf1c40f
            )
            embed.add_field(name="👤 المستخدم", value=f"<@{data['user_id']}>", inline=False)
            embed.add_field(name="💎 النقاط", value=data["points"], inline=True)
            embed.add_field(name="💳 الطريقة", value=data["method"], inline=True)
            embed.add_field(
                name="💰 المبلغ",
                value=f"{data['points'] / 100:.2f} جنيه",
                inline=False
            )
            embed.set_footer(text=f"ID: {req_id}")

            await ch.send(embed=embed, file=file, view=AdminView(req_id))

            data["status"] = "pending_admin"
            save_json(DEPOSIT_FILE, deposits)
            return
