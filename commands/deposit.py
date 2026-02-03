import discord
from discord import app_commands
from discord.ui import View, Button
from discord.ext import commands
import uuid
import json
import os

# ========= CONFIG =========
ADMIN_CHANNEL_ID = 1293008901142351952
VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"
PROBOT_ID = "802148738939748373"

PRICE_PER_1000 = 10  # 10 جنيه لكل 1000 نقطة
PROBOT_FEE_RATE = 0.053  # 5.3%

DATA_FILE = "data/deposits.json"
# ==========================


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ================== VIEW ==================

class PaymentView(View):
    def __init__(self, user_id, points, req_id):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.points = points
        self.req_id = req_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ هذا الطلب ليس لك", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Vodafone Cash", style=discord.ButtonStyle.primary, emoji="📱")
    async def vodafone(self, interaction: discord.Interaction, button: Button):
        await self.process(interaction, "Vodafone")

    @discord.ui.button(label="InstaPay", style=discord.ButtonStyle.success, emoji="💳")
    async def instapay(self, interaction: discord.Interaction, button: Button):
        await self.process(interaction, "InstaPay")

    @discord.ui.button(label="ProBot", style=discord.ButtonStyle.secondary, emoji="🤖")
    async def probot(self, interaction: discord.Interaction, button: Button):
        await self.process(interaction, "ProBot")

    async def process(self, interaction, method):
        deposits = load_data()

        base_price = (self.points / 1000) * PRICE_PER_1000
        final_price = base_price

        if method == "ProBot":
            final_price = int(base_price * (1 + PROBOT_FEE_RATE))

        deposits[self.req_id]["method"] = method
        deposits[self.req_id]["amount"] = final_price
        save_data(deposits)

        text = f"""
🧾 **تفاصيل الدفع**
💎 النقاط: {self.points}
💰 المبلغ: {final_price}

"""
        if method == "Vodafone":
            text += f"📱 حول على: `{VODAFONE_NUMBER}`"
        elif method == "InstaPay":
            text += f"💳 حول على: `{INSTAPAY_NUMBER}`"
        else:
            text += f"🤖 ProBot ID: `{PROBOT_ID}`"

        text += "\n\n📎 ابعت صورة إثبات التحويل هنا"

        await interaction.response.edit_message(content=text, view=None)


# ================== COMMAND ==================

@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    if points < 1000:
        await interaction.response.send_message(
            "❌ أقل شحن 1000 نقطة", ephemeral=True
        )
        return

    req_id = uuid.uuid4().hex[:8]

    deposits = load_data()
    deposits[req_id] = {
        "user_id": interaction.user.id,
        "points": points,
        "status": "waiting",
        "method": None,
        "amount": 0
    }
    save_data(deposits)

    embed = discord.Embed(
        title="💳 شحن رصيد",
        color=0x2f3136
    )
    embed.add_field(name="💎 النقاط", value=str(points))
    embed.set_footer(text=f"ID: {req_id}")

    await interaction.response.send_message(
        embed=embed,
        view=PaymentView(interaction.user.id, points, req_id),
        ephemeral=True
    )


# ================== PROOF HANDLER ==================

async def handle_proof_message(message: discord.Message):
    if not message.attachments:
        return

    deposits = load_data()

    for req_id, data in deposits.items():
        if data["user_id"] == message.author.id and data["status"] == "waiting":
            data["status"] = "review"
            save_data(deposits)

            try:
                await message.delete()
            except:
                pass

            await message.channel.send(
                "⏳ تم استلام إثبات التحويل\nطلبك الآن تحت المراجعة ✅",
                delete_after=15
            )

            admin_ch = message.guild.get_channel(ADMIN_CHANNEL_ID)
            if not admin_ch:
                return

            embed = discord.Embed(
                title="📥 طلب إيداع جديد",
                color=0xf1c40f
            )
            embed.add_field(name="👤 المستخدم", value=message.author.mention)
            embed.add_field(name="💎 النقاط", value=data["points"])
            embed.add_field(name="💰 المبلغ", value=data["amount"])
            embed.add_field(name="💳 الطريقة", value=data["method"])
            embed.set_footer(text=f"ID: {req_id}")

            file = await message.attachments[0].to_file()
            await admin_ch.send(embed=embed, file=file)

            return
