import discord
from discord import app_commands
import json
import os
import uuid

# ================== SETTINGS ==================
ADMIN_ACTION_CHANNEL_ID = 1293008901142351952

VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"
PROBOT_OWNER_ID = 802148738939748373

PRICE_PER_1000 = 1000
DATA_FILE = "data/deposits.json"

# ================== TEMP ==================
pending_deposits = {}

# ================== HELPERS ==================
def save_deposit(data):
    os.makedirs("data", exist_ok=True)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
    else:
        all_data = {}

    all_data[data["deposit_id"]] = data
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

def calc_price(points):
    return (points // 1000) * PRICE_PER_1000

# ================== SLASH ==================
@app_commands.command(name="deposit", description="شحن رصيد")
@app_commands.describe(points="عدد النقاط")
async def deposit(interaction: discord.Interaction, points: int):

    if points < 1000 or points % 1000 != 0:
        await interaction.response.send_message(
            "⛔ الحد الأدنى 1000 نقطة ومضاعفاتها فقط",
            ephemeral=True
        )
        return

    amount = calc_price(points)
    deposit_id = uuid.uuid4().hex[:8]

    # رسالة تعليمات (Only you)
    await interaction.response.send_message(
        f"🧾 **طلب شحن جديد**\n"
        f"🆔 ID: `{deposit_id}`\n"
        f"💎 النقاط: `{points}`\n"
        f"💵 المبلغ: `{amount}`\n\n"
        f"📲 فودافون: `{VODAFONE_NUMBER}`\n"
        f"🏦 إنستا باي: `{INSTAPAY_NUMBER}`\n"
        f"🤖 ProBot: `{PROBOT_OWNER_ID}`\n\n"
        f"📎 **ابعت صورة إثبات التحويل كرسالة عادية في الروم**",
        ephemeral=True
    )

    # رسالة عامة نربطها بالصورة
    public_msg = await interaction.channel.send(
        f"📎 <@{interaction.user.id}> ابعت صورة إثبات التحويل هنا"
    )

    pending_deposits[str(interaction.user.id)] = {
        "deposit_id": deposit_id,
        "user_id": interaction.user.id,
        "points": points,
        "amount": amount,
        "message": public_msg
    }

# ================== IMAGE HANDLER ==================
async def handle_proof_message(message: discord.Message):

    if message.author.bot or not message.attachments:
        return

    uid = str(message.author.id)
    if uid not in pending_deposits:
        return

    attachment = message.attachments[0]
    if not attachment.content_type or not attachment.content_type.startswith("image"):
        return

    data = pending_deposits[uid]

    # حذف صورة المستخدم
    await message.delete()

    # تعديل الرسالة العامة
    await data["message"].edit(
        content="⏳ **تم استلام الإثبات – في انتظار مراجعة الأدمن**"
    )

    # إرسال الطلب لروم الأدمن
    admin_channel = message.guild.get_channel(ADMIN_ACTION_CHANNEL_ID)
    if admin_channel:
        embed = discord.Embed(
            title="💰 طلب شحن جديد",
            color=0xf1c40f
        )
        embed.add_field(name="🆔 ID", value=data["deposit_id"], inline=False)
        embed.add_field(name="👤 المستخدم", value=f"<@{data['user_id']}>", inline=False)
        embed.add_field(name="💎 النقاط", value=str(data["points"]), inline=True)
        embed.add_field(name="💵 المبلغ", value=str(data["amount"]), inline=True)
        embed.set_image(url=attachment.url)

        await admin_channel.send(embed=embed)

    save_deposit(data)
    del pending_deposits[uid]
