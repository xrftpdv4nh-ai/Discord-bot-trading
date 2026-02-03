import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import json
import os
import uuid

# ================== CONFIG ==================
ADMIN_ACTION_CHANNEL_ID = 1293008901142351952

VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"
PROBOT_ID = 802148738939748373

PRICE_PER_1000 = 10  # 1000 نقطة = 10 جنيه
PROBOT_TAX_RATE = 0.053  # 5.3%

DATA_DIR = "data"
DEPOSIT_FILE = f"{DATA_DIR}/deposits.json"
WALLET_FILE = f"{DATA_DIR}/wallets.json"

os.makedirs(DATA_DIR, exist_ok=True)

# ================== HELPERS ==================
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

# ================== VIEW ==================
class DepositView(View):
    def __init__(self, req_id: str):
        super().__init__(timeout=None)
        self.req_id = req_id

    async def _finalize(self, interaction: discord.Interaction, accepted: bool):
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
        else:
            if user:
                try:
                    await user.send("❌ تم رفض طلب الشحن")
                except:
                    pass

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(view=self)

        del deposits[self.req_id]
        save_json(DEPOSIT_FILE, deposits)

        await interaction.followup.send(
            "✅ تم تنفيذ الإجراء" if accepted else "🚫 تم رفض الطلب",
            ephemeral=True
        )

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await self._finalize(interaction, True)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: Button):
        await self._finalize(interaction, False)

# ================== SLASH COMMAND ==================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):
    if points <= 0:
        await interaction.response.send_message("❌ عدد نقاط غير صحيح", ephemeral=True)
        return

    req_id = uuid.uuid4().hex[:8]
    price = (points / 1000) * PRICE_PER_1000

    data = {
        "user_id": interaction.user.id,
        "points": points,
        "price": price,
        "method": None
    }

    deposits = load_json(DEPOSIT_FILE, {})
    deposits[req_id] = data
    save_json(DEPOSIT_FILE, deposits)

    embed = discord.Embed(
        title="💳 شحن رصيد",
        color=0x5865F2
    )
    embed.add_field(name="💎 النقاط", value=str(points), inline=False)
    embed.add_field(name="💰 السعر", value=f"{price:.2f} جنيه", inline=False)
    embed.set_footer(text=f"ID: {req_id}")

    view = View()

    async def choose_method(method: str):
        deposits = load_json(DEPOSIT_FILE, {})
        deposits[req_id]["method"] = method

        final_price = price
        note = ""
        if method == "ProBot":
            final_price = price * (1 + PROBOT_TAX_RATE)
            note = f"\n⚠️ شامل ضريبة ProBot ({PROBOT_TAX_RATE*100:.1f}%)"

        save_json(DEPOSIT_FILE, deposits)

        await interaction.followup.send(
            f"📌 **طريقة الدفع:** {method}\n"
            f"💰 **المطلوب:** {final_price:.2f} جنيه{note}\n\n"
            f"📎 ابعت **صورة إثبات التحويل** كرسالة عادية هنا",
            ephemeral=True
        )

    async def vodafone_callback(i: discord.Interaction):
        await i.response.defer(ephemeral=True)
        await choose_method("Vodafone")

    async def instapay_callback(i: discord.Interaction):
        await i.response.defer(ephemeral=True)
        await choose_method("InstaPay")

    async def probot_callback(i: discord.Interaction):
        await i.response.defer(ephemeral=True)
        await choose_method("ProBot")

    v_btn = Button(label="Vodafone Cash", style=discord.ButtonStyle.primary)
    i_btn = Button(label="InstaPay", style=discord.ButtonStyle.success)
    p_btn = Button(label="ProBot", style=discord.ButtonStyle.secondary)

    v_btn.callback = vodafone_callback
    i_btn.callback = instapay_callback
    p_btn.callback = probot_callback

    view.add_item(v_btn)
    view.add_item(i_btn)
    view.add_item(p_btn)

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ================== PROOF HANDLER ==================
async def handle_proof_message(message: discord.Message):
    if not message.attachments:
        return

    deposits = load_json(DEPOSIT_FILE, {})
    for req_id, data in deposits.items():
        if data["user_id"] == message.author.id and data["method"]:
            attachment = message.attachments[0]
            file = await attachment.to_file(filename="proof.png")

            try:
                await message.delete()
            except:
                pass

            await message.channel.send(
                "⏳ تم استلام إثبات التحويل\nطلبك **تحت المراجعة** ✅",
                delete_after=15
            )

            channel = message.guild.get_channel(ADMIN_ACTION_CHANNEL_ID)
            if not channel:
                return

            embed = discord.Embed(
                title="📥 طلب إيداع جديد",
                color=0xF1C40F
            )
            embed.add_field(name="👤 المستخدم", value=message.author.mention, inline=False)
            embed.add_field(name="💎 النقاط", value=str(data["points"]), inline=False)
            embed.add_field(name="💳 الطريقة", value=data["method"], inline=False)
            embed.set_image(url="attachment://proof.png")
            embed.set_footer(text=f"ID: {req_id}")

            await channel.send(
                embed=embed,
                file=discord.File(file.fp, filename="proof.png"),
                view=DepositView(req_id)
            )
            break
