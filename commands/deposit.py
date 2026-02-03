import discord
from discord import app_commands
from discord.ui import View, Button, Select
import json
import os
import uuid
# تأكيد وجود فولدر data
os.makedirs("data", exist_ok=True)

# ================== CONFIG ==================
VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"
PROBOT_OWNER_ID = 802148738939748373

ADMIN_ROLE_ID = 1292973462091989155
ADMIN_ACTION_CHANNEL_ID = 1293008901142351952
LOG_CHANNEL_ID = 1293146723417587763

DATA_FILE = "data/deposits.json"

# ===== PRICING =====
POINT_PRICE_EGP = 20      # كل 1000 نقطة = 20 جنيه
POINT_PRICE_PROBOT = 1   # 1 نقطة = 1 ProBot


# ================== STORAGE ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ================== USER VIEW ==================
class DepositView(View):
    def __init__(self, user, amount):
        super().__init__(timeout=600)
        self.user = user
        self.amount = amount
        self.deposit_id = str(uuid.uuid4())[:8]

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("⛔ الطلب مش ليك", ephemeral=True)
            return False
        return True

    @discord.ui.select(
        placeholder="اختر طريقة الشحن",
        options=[
            discord.SelectOption(label="ProBot Credit", emoji="🤖"),
            discord.SelectOption(label="Vodafone Cash", emoji="💳"),
            discord.SelectOption(label="InstaPay", emoji="🏦")
        ]
    )
    async def select_method(self, interaction, select: Select):
        method = select.values[0]

        probot_amount = self.amount * POINT_PRICE_PROBOT
        egp_amount = int((self.amount / 1000) * POINT_PRICE_EGP)

        if method == "ProBot Credit":
            pay_text = (
                f"🤖 **المطلوب تحويله:** `{probot_amount}` ProBot Credit\n"
                f"👤 إلى ID: `{PROBOT_OWNER_ID}`\n"
                "⚠️ **ضريبة التحويل على المرسل**"
            )
        elif method == "Vodafone Cash":
            pay_text = (
                f"💳 **المطلوب تحويله:** `{egp_amount} جنيه`\n"
                f"📱 الرقم: `{VODAFONE_NUMBER}`"
            )
        else:
            pay_text = (
                f"🏦 **المطلوب تحويله:** `{egp_amount} جنيه`\n"
                f"📱 الرقم: `{INSTAPAY_NUMBER}`"
            )

        data = load_data()
        data[self.deposit_id] = {
            "user_id": interaction.user.id,
            "points": self.amount,
            "method": method,
            "status": "waiting_proof",
            "proof": None
        }
        save_data(data)

        embed = discord.Embed(
            title="💰 تفاصيل الشحن",
            description=(
                f"🆔 **ID الطلب:** `{self.deposit_id}`\n"
                f"🎯 **عدد النقاط:** `{self.amount}`\n\n"
                f"{pay_text}\n\n"
                "📎 **ابعت صورة إثبات التحويل الآن**"
            ),
            color=0xf39c12
        )

        await interaction.response.edit_message(embed=embed, view=None)

        await interaction.followup.send(
            "📎 **ابعت صورة إثبات التحويل هنا (صورة واحدة فقط)**",
            ephemeral=False
        )


# ================== ADMIN VIEW ==================
class AdminView(View):
    def __init__(self, deposit_id):
        super().__init__(timeout=None)
        self.deposit_id = deposit_id

    async def interaction_check(self, interaction):
        role = interaction.guild.get_role(ADMIN_ROLE_ID)
        if role not in interaction.user.roles:
            await interaction.response.send_message("⛔ مفيش صلاحية", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction, button):
        await handle_decision(interaction, self.deposit_id, True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction, button):
        await handle_decision(interaction, self.deposit_id, False)


# ================== PROOF HANDLER ==================
async def handle_proof_message(message):
    if message.author.bot or not message.attachments:
        return

    data = load_data()

    for deposit_id, entry in reversed(list(data.items())):
        if entry["user_id"] == message.author.id and entry["status"] == "waiting_proof":

            proof_url = message.attachments[0].url
            entry["proof"] = proof_url
            entry["status"] = "pending"
            save_data(data)

            # حذف صورة الإثبات
            await message.delete()

            # إرسال الطلب لروم القبول (مضمون)
            admin_channel = await message.client.fetch_channel(ADMIN_ACTION_CHANNEL_ID)

            embed = discord.Embed(
                title="🧾 طلب شحن جديد",
                description=(
                    f"👤 <@{entry['user_id']}>\n"
                    f"🎯 **النقاط:** `{entry['points']}`\n"
                    f"💳 **الطريقة:** `{entry['method']}`\n"
                    f"🆔 `{deposit_id}`"
                ),
                color=0x3498db
            )
            embed.set_image(url=proof_url)

            await admin_channel.send(
                embed=embed,
                view=AdminView(deposit_id)
            )
            break


# ================== ADMIN ACTION ==================
async def handle_decision(interaction, deposit_id, approve):
    data = load_data()
    if deposit_id not in data:
        await interaction.response.send_message("❌ الطلب غير موجود", ephemeral=True)
        return

    entry = data[deposit_id]
    entry["status"] = "approved" if approve else "rejected"
    save_data(data)

    if approve:
        from commands.wallet import load_wallets, save_wallets
        wallets = load_wallets()
        uid = str(entry["user_id"])
        wallets.setdefault(uid, {"balance": 0})
        wallets[uid]["balance"] += entry["points"]
        save_wallets(wallets)

    log = await interaction.client.fetch_channel(LOG_CHANNEL_ID)
    await log.send(
        f"{'✅ قبول' if approve else '❌ رفض'} شحن\n"
        f"👤 <@{entry['user_id']}>\n"
        f"🎯 `{entry['points']}` نقطة\n"
        f"🆔 `{deposit_id}`"
    )

    await interaction.response.send_message("✔️ تم تنفيذ القرار", ephemeral=True)


# ================== COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد / نقاط")
@app_commands.describe(amount="عدد النقاط (مثال: 1000)")
async def deposit(interaction, amount: int):
    if amount < 1000:
        await interaction.response.send_message(
            "⛔ الحد الأدنى للشحن **1000 نقطة**",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="💰 إنشاء طلب شحن",
        description=f"🎯 **عدد النقاط:** `{amount}`\n\nاختر طريقة الشحن:",
        color=0x2ecc71
    )

    await interaction.response.send_message(
        embed=embed,
        view=DepositView(interaction.user, amount),
        ephemeral=True
    )
