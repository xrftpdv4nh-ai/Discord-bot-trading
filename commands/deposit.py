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

USER_TIMEOUT_SECONDS = 600  # 10 دقائق

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


# ================== VIEW USER ==================
class DepositView(View):
    def __init__(self, user, amount):
        super().__init__(timeout=USER_TIMEOUT_SECONDS)
        self.user = user
        self.amount = amount
        self.deposit_id = str(uuid.uuid4())[:8]

    async def interaction_check(self, interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("⛔ الطلب مش ليك", ephemeral=True)
            return False
        return True

    @discord.ui.select(
        placeholder="اختر طريقة الإيداع",
        options=[
            discord.SelectOption(label="Vodafone Cash", emoji="💳"),
            discord.SelectOption(label="InstaPay", emoji="🏦"),
            discord.SelectOption(label="ProBot Credit", emoji="🤖")
        ]
    )
    async def select_method(self, interaction, select: Select):
        method = select.values[0]

        if method == "Vodafone Cash":
            instructions = f"💳 حول على الرقم:\n`{VODAFONE_NUMBER}`"
        elif method == "InstaPay":
            instructions = f"🏦 حول على الرقم:\n`{INSTAPAY_NUMBER}`"
        else:
            instructions = (
                f"🤖 حول ProBot Credit إلى:\n`{PROBOT_OWNER_ID}`\n\n"
                "⚠️ **ضريبة التحويل على المرسل**"
            )

        data = load_data()
        data[self.deposit_id] = {
            "user_id": interaction.user.id,
            "amount": self.amount,
            "method": method,
            "status": "waiting_proof",
            "proof": None
        }
        save_data(data)

        embed = discord.Embed(
            title="📎 إرسال إثبات التحويل",
            description=(
                f"🆔 **ID:** `{self.deposit_id}`\n"
                f"💰 **المبلغ:** `{self.amount}`\n"
                f"💳 **الطريقة:** `{method}`\n\n"
                f"{instructions}\n\n"
                "📎 **ابعت صورة إثبات التحويل (ريبلاي على الرسالة دي)**"
            ),
            color=0xe67e22
        )

        await interaction.response.edit_message(embed=embed, view=None)


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
    if message.author.bot:
        return
    if not message.attachments or not message.reference:
        return

    data = load_data()

    for deposit_id, entry in data.items():
        if entry["user_id"] == message.author.id and entry["status"] == "waiting_proof":
            entry["proof"] = message.attachments[0].url
            entry["status"] = "pending"
            save_data(data)

            # تعديل رسالة البوت
            try:
                bot_msg = await message.channel.fetch_message(message.reference.message_id)
                embed = bot_msg.embeds[0]
                embed.description = (
                    f"🆔 **ID:** `{deposit_id}`\n"
                    f"💰 **المبلغ:** `{entry['amount']}`\n"
                    f"💳 **الطريقة:** `{entry['method']}`\n\n"
                    "⏳ **في انتظار استلام الرصيد خلال 5 دقائق**"
                )
                embed.color = 0xf1c40f
                await bot_msg.edit(embed=embed)
            except:
                pass

            await message.delete()

            admin_channel = message.client.get_channel(ADMIN_ACTION_CHANNEL_ID)
            if admin_channel:
                emb = discord.Embed(
                    title="🧾 طلب إيداع",
                    description=(
                        f"👤 <@{entry['user_id']}>\n"
                        f"💰 `{entry['amount']}`\n"
                        f"💳 `{entry['method']}`\n"
                        f"🆔 `{deposit_id}`"
                    ),
                    color=0x3498db
                )
                emb.set_image(url=entry["proof"])
                await admin_channel.send(embed=emb, view=AdminView(deposit_id))
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
        wallets[uid]["balance"] += entry["amount"]
        save_wallets(wallets)

    user = interaction.client.get_user(entry["user_id"])
    if user:
        try:
            await user.send(
                f"{'✅ تم قبول' if approve else '❌ تم رفض'} الإيداع\n"
                f"💰 `{entry['amount']}`"
            )
        except:
            pass

    log = interaction.client.get_channel(LOG_CHANNEL_ID)
    if log:
        await log.send(
            f"{'✅ قبول' if approve else '❌ رفض'} إيداع\n"
            f"👤 <@{entry['user_id']}>\n"
            f"💰 `{entry['amount']}`\n"
            f"🆔 `{deposit_id}`"
        )

    await interaction.response.send_message("✔️ تم", ephemeral=True)


# ================== COMMAND ==================
@app_commands.command(name="deposit", description="طلب إيداع رصيد")
@app_commands.describe(amount="مبلغ الإيداع")
async def deposit(interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ مبلغ غير صالح", ephemeral=True)
        return

    embed = discord.Embed(
        title="💰 إنشاء طلب إيداع",
        description=f"💰 **المبلغ:** `{amount}`\n\nاختر طريقة الإيداع:",
        color=0x2ecc71
    )

    await interaction.response.send_message(
        embed=embed,
        view=DepositView(interaction.user, amount),
        ephemeral=True
    )
