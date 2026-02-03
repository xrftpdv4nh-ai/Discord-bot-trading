import discord
from discord import app_commands
from discord.ui import View, Button
import uuid
import json
import os

from config import (
    ADMIN_ACTION_CHANNEL_ID,
    LOG_CHANNEL_ID,
    VODAFONE_NUMBER,
    INSTAPAY_NUMBER,
    PROBOT_ID,
    PROBOT_FEE_RATE
)

WALLET_FILE = "data/wallets.json"
DEPOSIT_FILE = "data/deposits.json"


# ================== Utils ==================

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_balance(user_id: int, amount: int):
    wallets = load_json(WALLET_FILE, {})
    uid = str(user_id)
    wallets[uid] = wallets.get(uid, 0) + amount
    save_json(WALLET_FILE, wallets)


# ================== Admin Buttons ==================

class AdminDecisionView(View):
    def __init__(self, req_id: str):
        super().__init__(timeout=None)
        self.req_id = req_id

    async def disable_all(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        deposits = load_json(DEPOSIT_FILE, {})
        if self.req_id not in deposits:
            await interaction.response.send_message("❌ الطلب غير موجود", ephemeral=True)
            return

        data = deposits[self.req_id]
        add_balance(data["user_id"], data["points"])

        user = interaction.client.get_user(data["user_id"])
        if user:
            try:
                await user.send(f"✅ تم شحن **{data['points']} نقطة** بنجاح 💎")
            except:
                pass

        await self.disable_all()
        await interaction.message.edit(view=self)

        del deposits[self.req_id]
        save_json(DEPOSIT_FILE, deposits)

        await interaction.response.send_message("✅ تم قبول الطلب", ephemeral=True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: Button):
        deposits = load_json(DEPOSIT_FILE, {})
        if self.req_id not in deposits:
            await interaction.response.send_message("❌ الطلب غير موجود", ephemeral=True)
            return

        data = deposits[self.req_id]
        user = interaction.client.get_user(data["user_id"])
        if user:
            try:
                await user.send("❌ تم رفض طلب الإيداع الخاص بك")
            except:
                pass

        await self.disable_all()
        await interaction.message.edit(view=self)

        del deposits[self.req_id]
        save_json(DEPOSIT_FILE, deposits)

        await interaction.response.send_message("❌ تم رفض الطلب", ephemeral=True)


# ================== Proof Handler ==================

async def handle_proof_message(message: discord.Message):
    if not message.attachments:
        return

    deposits = load_json(DEPOSIT_FILE, {})
    for req_id, data in list(deposits.items()):
        if data["user_id"] != message.author.id or data.get("proof_sent"):
            continue

        data["proof_sent"] = True
        deposits[req_id] = data
        save_json(DEPOSIT_FILE, deposits)

        file = await message.attachments[0].to_file()

        admin_channel = message.guild.get_channel(ADMIN_ACTION_CHANNEL_ID)
        if not admin_channel:
            return

        embed = discord.Embed(
            title="📥 طلب إيداع جديد",
            color=0x2f3136
        )
        embed.add_field(name="👤 المستخدم", value=message.author.mention, inline=False)
        embed.add_field(name="💎 النقاط", value=str(data["points"]), inline=True)
        embed.add_field(name="💰 المبلغ", value=str(data["amount"]), inline=True)
        embed.add_field(name="💳 الطريقة", value=data["method"], inline=False)
        embed.set_footer(text=f"ID: {req_id}")

        view = AdminDecisionView(req_id)

        await admin_channel.send(embed=embed, file=file, view=view)

        try:
            await message.delete()
        except:
            pass

        await message.channel.send(
            "⏳ **تم استلام إثبات التحويل**\nطلبك الآن تحت المراجعة ✅",
            delete_after=15
        )
        break


# ================== Slash Command ==================

@app_commands.command(name="deposit", description="شحن رصيد")
async def deposit(interaction: discord.Interaction, points: int):
    if points <= 0:
        await interaction.response.send_message("❌ عدد نقاط غير صالح", ephemeral=True)
        return

    req_id = uuid.uuid4().hex[:8]

    embed = discord.Embed(
        title="💳 شحن رصيد",
        color=0x5865F2
    )
    embed.add_field(name="💎 النقاط", value=str(points), inline=False)
    embed.set_footer(text=f"ID: {req_id}")

    view = View(timeout=60)

    async def choose(method: str):
        deposits = load_json(DEPOSIT_FILE, {})
        amount = points / 100

        if method == "ProBot":
            amount = round((points * (1 + PROBOT_FEE_RATE)) / 100, 2)

        deposits[req_id] = {
            "user_id": interaction.user.id,
            "points": points,
            "amount": amount,
            "method": method,
            "proof_sent": False
        }
        save_json(DEPOSIT_FILE, deposits)

        text = (
            f"📎 ابعت صورة إثبات التحويل هنا\n\n"
            f"💰 المبلغ: **{amount}**\n"
        )
        if method == "Vodafone":
            text += f"📱 فودافون كاش: `{VODAFONE_NUMBER}`"
        elif method == "InstaPay":
            text += f"🏦 إنستا باي: `{INSTAPAY_NUMBER}`"
        else:
            text += f"🤖 ProBot ID: `{PROBOT_ID}`"

        await interaction.edit_original_response(content=text, embed=None, view=None)

    view.add_item(Button(label="Vodafone Cash", style=discord.ButtonStyle.primary, custom_id="vod"))
    view.add_item(Button(label="InstaPay", style=discord.ButtonStyle.success, custom_id="insta"))
    view.add_item(Button(label="ProBot", style=discord.ButtonStyle.secondary, custom_id="probot"))

    async def interaction_check(i: discord.Interaction):
        if i.user.id != interaction.user.id:
            await i.response.send_message("❌ هذا الطلب ليس لك", ephemeral=True)
            return False
        return True

    view.interaction_check = interaction_check

    async def callback(i: discord.Interaction):
        cid = i.data["custom_id"]
        if cid == "vod":
            await choose("Vodafone")
        elif cid == "insta":
            await choose("InstaPay")
        else:
            await choose("ProBot")

    for item in view.children:
        item.callback = callback

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
