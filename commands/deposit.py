import discord
from discord import app_commands
from discord.ui import View, Button
import uuid
from datetime import datetime

from config import (
    ADMIN_ACTION_CHANNEL_ID,
    LOG_CHANNEL_ID,
    VODAFONE_NUMBER,
    INSTAPAY_NUMBER,
    PROBOT_ID,
    DEPOSIT_CHANNEL_ID
)

# ================== PAYMENT VIEW ==================
class PaymentView(View):
    def __init__(self, points, req_id):
        super().__init__(timeout=300)
        self.points = points
        self.req_id = req_id

    async def _select(self, interaction: discord.Interaction, method: str):
        await interaction.response.defer(ephemeral=True)

        deposits = interaction.client.deposits

        await deposits.update_one(
            {"req_id": self.req_id},
            {
                "$set": {
                    "method": method,
                    "status": "waiting_proof"
                }
            }
        )

        amount_egp = self.points / 100

        if method == "Vodafone Cash":
            text = f"📱 حول **{amount_egp:.2f} جنيه** على:\n`{VODAFONE_NUMBER}`"
        elif method == "InstaPay":
            text = f"💳 حول **{amount_egp:.2f} جنيه** على:\n`{INSTAPAY_NUMBER}`"
        else:
            text = f"🤖 ابعت **{self.points} نقطة** إلى:\n`{PROBOT_ID}`"

        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            content=f"{text}\n\n📎 ابعت صورة إثبات التحويل هنا",
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
        await interaction.response.defer()

        deposits = interaction.client.deposits
        wallets = interaction.client.wallets

        data = await deposits.find_one({"req_id": self.req_id})
        if not data:
            return

        user = interaction.client.get_user(data["user_id"])
        log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)

        if accepted:
            await wallets.update_one(
                {"user_id": data["user_id"]},
                {
                    "$inc": {
                        "balance": data["points"],
                        "total_deposit": data["points"]
                    },
                    "$set": {
                        "last_update": str(datetime.now())
                    }
                },
                upsert=True
            )

            if user:
                try:
                    await user.send(
                        f"✅ تم شحن رصيدك بنجاح\n"
                        f"💎 النقاط: {data['points']}\n"
                        f"🧾 رقم الطلب: {self.req_id}"
                    )
                except:
                    pass

            if log_channel:
                await log_channel.send(
                    f"✅ Deposit Accepted\n"
                    f"👤 <@{data['user_id']}>\n"
                    f"💎 {data['points']} نقطة\n"
                    f"🧾 {self.req_id}"
                )

        else:
            if user:
                try:
                    await user.send(
                        f"❌ تم رفض طلب الشحن\n"
                        f"🧾 رقم الطلب: {self.req_id}"
                    )
                except:
                    pass

        for c in self.children:
            c.disabled = True

        await interaction.message.edit(view=self)

        await deposits.delete_one({"req_id": self.req_id})


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

    await interaction.response.defer(ephemeral=True)

    if interaction.channel.id != DEPOSIT_CHANNEL_ID:
        await interaction.followup.send(
            "🚫 This channel is for deposits only.",
            ephemeral=True
        )
        return

    req_id = uuid.uuid4().hex[:8]

    deposits = interaction.client.deposits

    await deposits.insert_one({
        "req_id": req_id,
        "user_id": interaction.user.id,
        "points": points,
        "method": None,
        "status": "choose_method",
        "created_at": datetime.utcnow()
    })

    embed = discord.Embed(
        title="💳 شحن رصيد",
        description=(
            f"💎 النقاط: {points}\n"
            f"💰 المبلغ: {points / 100:.2f} جنيه\n\n"
            "اختر طريقة الدفع:"
        ),
        color=0x2ecc71
    )
    embed.set_footer(text=f"ID: {req_id}")

    await interaction.followup.send(
        embed=embed,
        view=PaymentView(points, req_id),
        ephemeral=True
    )


# ================== PROOF HANDLER ==================
async def handle_proof_message(message: discord.Message):
    if not message.attachments or not message.guild:
        return

    deposits = message.client.deposits

    data = await deposits.find_one(
        {"user_id": message.author.id},
        sort=[("created_at", -1)]
    )

    if not data:
        return

    if not data.get("method"):
        await message.channel.send(
            "❌ لازم تختار طريقة الدفع الأول",
            delete_after=8
        )
        return

    req_id = data["req_id"]

    file = await message.attachments[0].to_file(filename="proof.png")

    try:
        await message.delete()
    except:
        pass

    await message.channel.send(
        "⏳ تم استلام إثبات التحويل\nطلبك تحت المراجعة 🔍",
        delete_after=10
    )

    admin_channel = message.guild.get_channel(ADMIN_ACTION_CHANNEL_ID)
    if not admin_channel:
        return

    embed = discord.Embed(title="📥 طلب إيداع جديد", color=0xf1c40f)
    embed.add_field(name="👤 المستخدم", value=message.author.mention, inline=False)
    embed.add_field(name="💎 النقاط", value=data["points"], inline=True)
    embed.add_field(name="💳 الطريقة", value=data["method"], inline=True)
    embed.set_footer(text=f"ID: {req_id}")
    embed.set_image(url="attachment://proof.png")

    await admin_channel.send(
        embed=embed,
        file=file,
        view=AdminView(req_id)
    )
