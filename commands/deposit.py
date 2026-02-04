import discord
from discord import app_commands
from discord.ext import commands
import json
import uuid
import os

# ================== CONFIG ==================
ADMIN_CHANNEL_ID = 1293008901142351952
DEPOSIT_FILE = "data/deposits.json"

VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"
PROBOT_ID = "802148738939748373"

# ================== JSON HELPERS ==================
def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================== BALANCE ==================
def add_balance(user_id: int, amount: int):
    path = "data/wallets.json"
    wallets = load_json(path, {})
    uid = str(user_id)
    wallets[uid] = wallets.get(uid, 0) + amount
    save_json(path, wallets)

# ================== VIEW ==================
class DepositView(discord.ui.View):
    def __init__(self, req_id: str):
        super().__init__(timeout=None)
        self.req_id = req_id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finalize(interaction, accepted=True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._finalize(interaction, accepted=False)

    async def _finalize(self, interaction: discord.Interaction, accepted: bool):
        if not interaction.response.is_done():
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

            result_text = "✅ تم قبول الطلب وشحن الرصيد"

        else:
            if user:
                try:
                    await user.send("❌ **تم رفض طلب الشحن**")
                except:
                    pass

            result_text = "🚫 تم رفض الطلب"

        # تعطيل الأزرار
        for item in self.children:
            item.disabled = True

        await interaction.message.edit(view=self)

        del deposits[self.req_id]
        save_json(DEPOSIT_FILE, deposits)

        await interaction.followup.send(result_text, ephemeral=True)

# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    if points <= 0:
        await interaction.response.send_message("❌ رقم غير صالح", ephemeral=True)
        return

    req_id = uuid.uuid4().hex[:8]

    deposits = load_json(DEPOSIT_FILE, {})
    deposits[req_id] = {
        "user_id": interaction.user.id,
        "points": points,
        "status": "waiting_proof"
    }
    save_json(DEPOSIT_FILE, deposits)

    embed = discord.Embed(
        title="💳 شحن رصيد",
        color=0x3498db
    )
    embed.add_field(name="💎 النقاط", value=str(points), inline=False)
    embed.add_field(
        name="طرق الدفع",
        value=(
            f"📱 **Vodafone Cash**: `{VODAFONE_NUMBER}`\n"
            f"🏦 **InstaPay**: `{INSTAPAY_NUMBER}`\n"
            f"🤖 **ProBot**: `{PROBOT_ID}`"
        ),
        inline=False
    )
    embed.set_footer(text=f"ID: {req_id}")

    await interaction.response.send_message(
        embed=embed,
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

            try:
                await message.delete()
            except:
                pass

            # رسالة للمستخدم
            try:
                await message.channel.send(
                    "⏳ **تم استلام إثبات التحويل**\n"
                    "طلبك الآن **تحت المراجعة** ✅",
                    delete_after=15
                )
            except:
                pass

            admin_channel = message.guild.get_channel(ADMIN_CHANNEL_ID)
            if not admin_channel:
                return

            embed = discord.Embed(
                title="📩 طلب إيداع جديد",
                color=0xf1c40f
            )
            embed.add_field(name="👤 المستخدم", value=message.author.mention, inline=False)
            embed.add_field(name="💎 النقاط", value=str(data["points"]), inline=False)
            embed.set_image(url=attachment.url)
            embed.set_footer(text=f"ID: {req_id}")

            data["status"] = "pending"
            save_json(DEPOSIT_FILE, deposits)

            await admin_channel.send(
                embed=embed,
                view=DepositView(req_id)
            )
            return
