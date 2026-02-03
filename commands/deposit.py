import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import uuid

from utils.json_db import load_json, save_json
from admin.wallet_admin import add_balance
from config import ADMIN_ACTION_CHANNEL_ID

DEPOSIT_FILE = "data/deposits.json"


# =========================
# VIEW: Confirm / Reject
# =========================
class DepositView(View):
    def __init__(self, req_id=None):
        super().__init__(timeout=None)
        self.req_id = req_id

    async def _finalize(self, interaction: discord.Interaction, accepted: bool):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        deposits = load_json(DEPOSIT_FILE, {})
        if not self.req_id or self.req_id not in deposits:
            await interaction.followup.send("❌ الطلب غير موجود", ephemeral=True)
            return

        data = deposits[self.req_id]
        user = interaction.client.get_user(data["user_id"])

        if accepted:
            add_balance(data["user_id"], data["points"])
            result_text = "✅ تم قبول الطلب وشحن الرصيد"

            if user:
                try:
                    await user.send(
                        f"✅ **تم شحن رصيدك بنجاح**\n"
                        f"💎 النقاط: {data['points']}"
                    )
                except:
                    pass
        else:
            result_text = "🚫 تم رفض الطلب"

            if user:
                try:
                    await user.send("❌ **تم رفض طلب الشحن**")
                except:
                    pass

        # تعطيل الأزرار (استخدام مرة واحدة)
        for item in self.children:
            item.disabled = True

        await interaction.message.edit(view=self)

        del deposits[self.req_id]
        save_json(DEPOSIT_FILE, deposits)

        await interaction.followup.send(result_text, ephemeral=True)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await self._finalize(interaction, True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await self._finalize(interaction, False)


# =========================
# SLASH COMMAND: /deposit
# =========================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    await interaction.response.defer(ephemeral=True)

    req_id = uuid.uuid4().hex[:8]

    deposits = load_json(DEPOSIT_FILE, {})
    deposits[req_id] = {
        "user_id": interaction.user.id,
        "points": points,
        "status": "waiting_payment"
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
        content="اختر طريقة الدفع:",
        view=PaymentMethodView(req_id),
        ephemeral=True
    )


# =========================
# VIEW: Payment Methods
# =========================
class PaymentMethodView(View):
    def __init__(self, req_id):
        super().__init__(timeout=120)
        self.req_id = req_id

    async def disable_all(self, interaction):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Vodafone Cash", style=discord.ButtonStyle.primary, emoji="📱")
    async def vodafone(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            "📤 **حوّل على Vodafone Cash:**\n`01009137618`\n\n"
            "📎 ابعت صورة إثبات التحويل في نفس الروم",
            ephemeral=True
        )
        await self.disable_all(interaction)

    @discord.ui.button(label="InstaPay", style=discord.ButtonStyle.success, emoji="💳")
    async def instapay(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            "📤 **حوّل على InstaPay:**\n`01124808116`\n\n"
            "📎 ابعت صورة إثبات التحويل في نفس الروم",
            ephemeral=True
        )
        await self.disable_all(interaction)

    @discord.ui.button(label="ProBot", style=discord.ButtonStyle.secondary, emoji="🤖")
    async def probot(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            "🤖 **تحويل ProBot Credit**\n"
            "⚠️ التحويل يشمل ضريبة بروبوت\n\n"
            "📎 ابعت صورة إثبات التحويل في نفس الروم",
            ephemeral=True
        )
        await self.disable_all(interaction)


# =========================
# PROOF HANDLER
# =========================
async def handle_proof_message(message: discord.Message):
    if not message.attachments:
        return

    deposits = load_json(DEPOSIT_FILE, {})

    for req_id, data in deposits.items():
        if data["user_id"] == message.author.id and data["status"] == "waiting_payment":
            file = await message.attachments[0].to_file()

            try:
                await message.delete()
            except:
                pass

            await message.channel.send(
                "⏳ **تم استلام إثبات التحويل**\n"
                "طلبك الآن **تحت المراجعة** ✅",
                delete_after=15
            )

            admin_channel = message.guild.get_channel(ADMIN_ACTION_CHANNEL_ID)
            if not admin_channel:
                return

            embed = discord.Embed(
                title="📥 طلب إيداع جديد",
                color=0xf1c40f
            )
            embed.add_field(name="👤 المستخدم", value=message.author.mention, inline=False)
            embed.add_field(name="💎 النقاط", value=str(data["points"]), inline=False)
            embed.set_footer(text=f"ID: {req_id}")

            view = DepositView(req_id)
            await admin_channel.send(embed=embed, file=file, view=view)

            data["status"] = "waiting_admin"
            save_json(DEPOSIT_FILE, deposits)
            break
