import discord
from discord import app_commands
from discord.ui import View, Button
import uuid

from admin.wallet_admin import add_balance
from utils.json_db import load_json, save_json

DEPOSIT_FILE = "data/deposits.json"
ADMIN_CHANNEL_ID = 1293008901142351952

# ===============================
# View اختيار طريقة الدفع
# ===============================
class PaymentView(View):
    def __init__(self, req_id: str):
        super().__init__(timeout=300)
        self.req_id = req_id

    @discord.ui.button(label="Vodafone Cash", style=discord.ButtonStyle.primary, emoji="📱")
    async def vodafone(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "Vodafone Cash")

    @discord.ui.button(label="InstaPay", style=discord.ButtonStyle.success, emoji="💳")
    async def instapay(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "InstaPay")

    @discord.ui.button(label="ProBot", style=discord.ButtonStyle.secondary, emoji="🤖")
    async def probot(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "ProBot")

    async def _select(self, interaction: discord.Interaction, method: str):
        deposits = load_json(DEPOSIT_FILE, {})
        if self.req_id not in deposits:
            await interaction.response.send_message("❌ الطلب غير موجود", ephemeral=True)
            return

        deposits[self.req_id]["method"] = method
        save_json(DEPOSIT_FILE, deposits)

        for c in self.children:
            c.disabled = True
        await interaction.message.edit(view=self)

        await interaction.response.send_message(
            f"📎 **تم اختيار طريقة الدفع:** {method}\n"
            "ابعت **صورة إثبات التحويل** في نفس الروم",
            ephemeral=True
        )


# ===============================
# View قبول / رفض الأدمن
# ===============================
class DepositView(View):
    def __init__(self, req_id: str):
        super().__init__(timeout=None)
        self.req_id = req_id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await self._finalize(interaction, accepted=True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await self._finalize(interaction, accepted=False)

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

        for c in self.children:
            c.disabled = True
        await interaction.message.edit(view=self)

        del deposits[self.req_id]
        save_json(DEPOSIT_FILE, deposits)

        await interaction.followup.send(result)


# ===============================
# Slash Command /deposit
# ===============================
@app_commands.command(name="deposit", description="شحن رصيد")
async def deposit(interaction: discord.Interaction, points: int):
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
        description=f"💎 النقاط: **{points}**\nاختر طريقة الدفع:",
        color=0x3498db
    )
    embed.set_footer(text=f"ID: {req_id}")

    await interaction.response.send_message(
        embed=embed,
        view=PaymentView(req_id),
        ephemeral=True
    )


# ===============================
# استقبال صورة الإثبات
# ===============================
async def handle_proof_message(message: discord.Message):
    if not message.attachments:
        return

    deposits = load_json(DEPOSIT_FILE, {})
    for req_id, data in deposits.items():
        if data["user_id"] == message.author.id and data["method"]:
            attachment = message.attachments[0]
            file = await attachment.to_file()

            embed = discord.Embed(
                title="📥 طلب إيداع جديد",
                color=0xf1c40f
            )
            embed.add_field(name="👤 المستخدم", value=message.author.mention)
            embed.add_field(name="💎 النقاط", value=str(data["points"]))
            embed.add_field(name="💳 الطريقة", value=data["method"])
            embed.set_image(url="attachment://proof.png")
            embed.set_footer(text=f"ID: {req_id}")

            admin_ch = message.guild.get_channel(ADMIN_CHANNEL_ID)
            if admin_ch:
                await admin_ch.send(
                    embed=embed,
                    file=discord.File(file.fp, filename="proof.png"),
                    view=DepositView(req_id)
                )

            try:
                await message.delete()
            except:
                pass

            try:
                await message.channel.send(
                    "⏳ **تم استلام إثبات التحويل**\n"
                    "طلبك تحت المراجعة وسيتم الرد عليك قريبًا ✅",
                    delete_after=15
                )
            except:
                pass
            break
