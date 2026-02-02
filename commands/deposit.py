import discord
from discord import app_commands
from discord.ui import View, Button, Select
import json
import os
import time
import uuid

# ================== CONFIG ==================
VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"
PROBOT_OWNER_ID = 802148738939748373

ADMIN_ROLE_ID = 1292973462091989155
ADMIN_ACTION_CHANNEL_ID = 1293008901142351952
LOG_CHANNEL_ID = 1293146723417587763

USER_TIMEOUT_SECONDS = 600  # 10 minutes

DATA_FILE = "data/deposits.json"


# ================== STORAGE ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ================== VIEWS ==================
class DepositMethodView(View):
    def __init__(self, user: discord.User, amount: int):
        super().__init__(timeout=USER_TIMEOUT_SECONDS)
        self.user = user
        self.amount = amount
        self.deposit_id = str(uuid.uuid4())[:8]
        self.created_at = int(time.time())
        self.method = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "⛔ هذا الطلب ليس لك",
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        data = load_data()
        if self.deposit_id in data:
            data[self.deposit_id]["status"] = "expired"
            save_data(data)

    @discord.ui.select(
        placeholder="اختر طريقة الإيداع",
        options=[
            discord.SelectOption(label="Vodafone Cash", emoji="💳"),
            discord.SelectOption(label="InstaPay", emoji="🏦"),
            discord.SelectOption(label="ProBot Credit", emoji="🤖")
        ]
    )
    async def select_method(self, interaction: discord.Interaction, select: Select):
        self.method = select.values[0]

        instructions = ""
        if self.method == "Vodafone Cash":
            instructions = f"📱 حول على الرقم:\n`{VODAFONE_NUMBER}`"
        elif self.method == "InstaPay":
            instructions = f"🏦 حول على الرقم:\n`{INSTAPAY_NUMBER}`"
        else:
            instructions = f"🤖 حول ProBot Credit إلى:\n`{PROBOT_OWNER_ID}`"

        data = load_data()
        data[self.deposit_id] = {
            "user_id": interaction.user.id,
            "amount": self.amount,
            "method": self.method,
            "status": "pending",
            "created_at": self.created_at
        }
        save_data(data)

        embed = discord.Embed(
            title="💰 طلب إيداع",
            description=(
                f"🆔 **ID:** `{self.deposit_id}`\n"
                f"💰 **المبلغ:** `{self.amount}`\n"
                f"💳 **الطريقة:** `{self.method}`\n\n"
                f"{instructions}\n\n"
                "⏱️ **أمامك 10 دقائق فقط للتحويل**"
            ),
            color=0x3498db
        )

        await interaction.response.edit_message(embed=embed, view=None)

        # إرسال للأدمن
        channel = interaction.client.get_channel(ADMIN_ACTION_CHANNEL_ID)
        if channel:
            await channel.send(
                embed=build_admin_embed(interaction.user, self.amount, self.method, self.deposit_id),
                view=AdminDecisionView(self.deposit_id)
            )


class AdminDecisionView(View):
    def __init__(self, deposit_id: str):
        super().__init__(timeout=None)
        self.deposit_id = deposit_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        role = interaction.guild.get_role(ADMIN_ROLE_ID)
        if role not in interaction.user.roles:
            await interaction.response.send_message(
                "⛔ ليس لديك صلاحية",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await handle_admin_action(interaction, self.deposit_id, approve=True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await handle_admin_action(interaction, self.deposit_id, approve=False)


# ================== HELPERS ==================
def build_admin_embed(user, amount, method, deposit_id):
    return discord.Embed(
        title="🧾 طلب إيداع جديد",
        description=(
            f"👤 {user.mention}\n"
            f"💰 المبلغ: `{amount}`\n"
            f"💳 الطريقة: `{method}`\n"
            f"🆔 ID: `{deposit_id}`"
        ),
        color=0xf1c40f
    )


async def handle_admin_action(interaction, deposit_id, approve: bool):
    data = load_data()
    if deposit_id not in data:
        await interaction.response.send_message("❌ الطلب غير موجود", ephemeral=True)
        return

    entry = data[deposit_id]
    entry["status"] = "approved" if approve else "rejected"
    save_data(data)

    user = interaction.client.get_user(entry["user_id"])
    if user:
        try:
            await user.send(
                f"💰 **تم {'قبول' if approve else 'رفض'} الإيداع**\n"
                f"🆔 `{deposit_id}`\n"
                f"💳 `{entry['method']}`\n"
                f"💰 `{entry['amount']}`"
            )
        except:
            pass

    log_channel = interaction.client.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(
            f"{'✅ قبول' if approve else '❌ رفض'} إيداع\n"
            f"👤 <@{entry['user_id']}>\n"
            f"💰 `{entry['amount']}`\n"
            f"🆔 `{deposit_id}`"
        )

    await interaction.response.send_message("✔️ تم تنفيذ القرار", ephemeral=True)


# ================== COMMAND ==================
@app_commands.command(name="deposit", description="طلب إيداع رصيد")
@app_commands.describe(amount="مبلغ الإيداع")
async def deposit(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ مبلغ غير صالح", ephemeral=True)
        return

    embed = discord.Embed(
        title="💰 إنشاء طلب إيداع",
        description=(
            f"💰 **المبلغ:** `{amount}`\n\n"
            "اختر طريقة الإيداع:"
        ),
        color=0x2ecc71
    )

    await interaction.response.send_message(
        embed=embed,
        view=DepositMethodView(interaction.user, amount),
        ephemeral=True
    )
