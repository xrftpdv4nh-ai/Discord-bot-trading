import discord
from discord import app_commands
import json
import uuid
import os

from config import (
    ADMIN_ACTION_CHANNEL_ID,
    VODAFONE_NUMBER,
    INSTAPAY_NUMBER,
    DATA_FILE
)

# =========================
# أدوات مساعدة
# =========================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# =========================
# Slash Command
# =========================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(
    method="طريقة الشحن",
    amount="عدد النقاط"
)
@app_commands.choices(
    method=[
        app_commands.Choice(name="Vodafone Cash", value="vodafone"),
        app_commands.Choice(name="InstaPay", value="instapay"),
    ]
)
async def deposit(interaction: discord.Interaction, method: app_commands.Choice[str], amount: int):
    deposit_id = uuid.uuid4().hex[:8]

    data = load_data()
    data[deposit_id] = {
        "user_id": interaction.user.id,
        "amount": amount,
        "method": method.value,
        "status": "waiting_proof",
        "request_message_id": None
    }
    save_data(data)

    number = VODAFONE_NUMBER if method.value == "vodafone" else INSTAPAY_NUMBER

    embed = discord.Embed(
        title="📎 إرسال إثبات التحويل",
        description=(
            f"**ID:** `{deposit_id}`\n"
            f"**المبلغ:** `{amount}` نقطة\n"
            f"**الطريقة:** `{method.name}`\n\n"
            f"🔢 **حوّل على الرقم:** `{number}`\n\n"
            "📷 **ابعت صورة إثبات التحويل**\n"
            "⚠️ **Reply على هذه الرسالة بالصورة فقط**"
        ),
        color=0xf1c40f
    )

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()

    data[deposit_id]["request_message_id"] = msg.id
    save_data(data)

# =========================
# التقاط صورة الإثبات
# =========================
async def handle_proof_message(message: discord.Message):
    if not message.reference:
        return

    if not message.attachments:
        return

    data = load_data()

    for dep_id, dep in data.items():
        if dep.get("request_message_id") == message.reference.message_id:
            if dep["status"] != "waiting_proof":
                return

            dep["status"] = "waiting_admin"
            dep["proof"] = message.attachments[0].url
            save_data(data)

            # حذف صورة المستخدم
            await message.delete()

            # تعديل رسالة الطلب
            try:
                original = await message.channel.fetch_message(dep["request_message_id"])
                new_embed = original.embeds[0]
                new_embed.description += "\n\n⏳ **في انتظار مراجعة الأدمن**"
                await original.edit(embed=new_embed)
            except:
                pass

            # إرسال الطلب لروم الأدمن
            admin_channel = message.guild.get_channel(ADMIN_ACTION_CHANNEL_ID)
            if admin_channel:
                admin_embed = discord.Embed(
                    title="💳 طلب شحن جديد",
                    description=(
                        f"**ID:** `{dep_id}`\n"
                        f"👤 <@{dep['user_id']}>\n"
                        f"💰 `{dep['amount']}` نقطة\n"
                        f"💳 `{dep['method']}`"
                    ),
                    color=0x3498db
                )
                admin_embed.set_image(url=dep["proof"])
                await admin_channel.send(embed=admin_embed)

            break
