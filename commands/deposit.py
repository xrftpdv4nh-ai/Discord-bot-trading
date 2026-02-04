import discord
from discord import app_commands
from discord.ext import commands
import json
import uuid

ADMIN_CHANNEL_ID = 1293008901142351952
DEPOSIT_FILE = "data/deposits.json"
WALLET_FILE = "data/wallets.json"


# ===================== أدوات JSON =====================
def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ===================== حساب السعر =====================
def calculate_amount(points, method):
    base = points / 100  # 1000 نقطة = 10 جنيه
    if method == "ProBot":
        return round(base * 1.053, 2)
    return round(base, 2)


# ===================== إضافة رصيد =====================
def add_balance(user_id, amount):
    wallets = load_json(WALLET_FILE, {})
    uid = str(user_id)
    wallets[uid] = int(wallets.get(uid, 0)) + int(amount)
    save_json(WALLET_FILE, wallets)


# ===================== View اختيار الدفع =====================
class PaymentView(discord.ui.View):
    def __init__(self, req_id):
        super().__init__(timeout=300)
        self.req_id = req_id

    async def select(self, interaction: discord.Interaction, method: str):
        await interaction.response.defer(ephemeral=True)

        deposits = load_json(DEPOSIT_FILE, {})
        data = deposits.get(self.req_id)
        if not data:
            return

        data["method"] = method
        data["amount"] = calculate_amount(data["points"], method)
        deposits[self.req_id] = data
        save_json(DEPOSIT_FILE, deposits)

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(view=self)

        await interaction.followup.send(
            f"💳 **طريقة الدفع:** {method}\n"
            f"💰 **المبلغ المطلوب:** {data['amount']} جنيه\n\n"
            f"📎 ابعت صورة إثبات التحويل في نفس الروم",
            ephemeral=True
        )

    @discord.ui.button(label="Vodafone Cash", style=discord.ButtonStyle.primary)
    async def vodafone(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select(interaction, "Vodafone Cash")

    @discord.ui.button(label="InstaPay", style=discord.ButtonStyle.success)
    async def instapay(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select(interaction, "InstaPay")

    @discord.ui.button(label="ProBot", style=discord.ButtonStyle.secondary)
    async def probot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.select(interaction, "ProBot")


# ===================== View الأدمن =====================
class AdminView(discord.ui.View):
    def __init__(self, req_id):
        super().__init__(timeout=None)
        self.req_id = req_id

    async def finalize(self, interaction: discord.Interaction, accepted: bool):
        await interaction.response.defer(ephemeral=True)

        deposits = load_json(DEPOSIT_FILE, {})
        data = deposits.get(self.req_id)
        if not data:
            return

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
            msg = "✅ تم قبول الطلب وشحن الرصيد"
        else:
            if user:
                try:
                    await user.send("❌ **تم رفض طلب الشحن**")
                except:
                    pass
            msg = "🚫 تم رفض الطلب"

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(view=self)

        del deposits[self.req_id]
        save_json(DEPOSIT_FILE, deposits)

        await interaction.followup.send(msg, ephemeral=True)

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.finalize(interaction, True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.finalize(interaction, False)


# ===================== Slash Command =====================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    if points <= 0:
        await interaction.response.send_message("❌ عدد النقاط غير صحيح", ephemeral=True)
        return

    req_id = uuid.uuid4().hex[:8]

    deposits = load_json(DEPOSIT_FILE, {})
    deposits[req_id] = {
        "user_id": interaction.user.id,
        "points": points,
        "status": "waiting_method"
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


# ===================== إثبات التحويل =====================
async def handle_proof_message(message: discord.Message):
    if not message.attachments:
        return

    deposits = load_json(DEPOSIT_FILE, {})

    for req_id, data in deposits.items():
        if data["user_id"] == message.author.id and "method" in data:
            attachment = message.attachments[0]
            file = await attachment.to_file()

            embed = discord.Embed(
                title="📥 طلب إيداع جديد",
                color=0xf1c40f
            )
            embed.add_field(name="👤 المستخدم", value=message.author.mention)
            embed.add_field(name="💎 النقاط", value=str(data["points"]))
            embed.add_field(name="💳 الطريقة", value=data["method"])
            embed.add_field(name="💰 المبلغ", value=f"{data['amount']} جنيه")
            embed.set_footer(text=f"ID: {req_id}")

            admin_channel = message.guild.get_channel(ADMIN_CHANNEL_ID)
            if admin_channel:
                await admin_channel.send(
                    embed=embed,
                    file=file,
                    view=AdminView(req_id)
                )

            try:
                await message.delete()
            except:
                pass

            await message.channel.send(
                "⏳ **تم استلام إثبات التحويل**\n"
                "طلبك الآن تحت المراجعة ✅",
                delete_after=15
            )
            break
