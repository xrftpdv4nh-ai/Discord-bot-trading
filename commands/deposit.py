import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import uuid

# ================== SETTINGS ==================
ADMIN_ACTION_CHANNEL_ID = 1293008901142351952
LOG_CHANNEL_ID = 1293146723417587763

VODAFONE_NUMBER = "01009137618"
INSTAPAY_NUMBER = "01124808116"
PROBOT_OWNER_ID = 802148738939748373

PRICE_PER_1000 = 1000  # 1000 نقطة = 1000 فلوس

DATA_FILE = "data/deposits.json"

# ================== TEMP STORAGE ==================
pending_deposits = {}

# ================== HELPERS ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def calc_price(points: int):
    return (points // 1000) * PRICE_PER_1000

def build_admin_embed(info, image_url):
    embed = discord.Embed(
        title="💰 طلب إيداع جديد",
        color=0xf1c40f
    )
    embed.add_field(name="🆔 ID", value=info["deposit_id"], inline=False)
    embed.add_field(name="👤 المستخدم", value=f"<@{info['user_id']}>", inline=False)
    embed.add_field(name="💎 النقاط", value=str(info["points"]), inline=True)
    embed.add_field(name="💵 المبلغ", value=str(info["amount"]), inline=True)
    embed.add_field(name="🏦 الطريقة", value=info["method"], inline=False)
    embed.set_image(url=image_url)
    embed.set_footer(text="اكتب: موافق / رفض")
    return embed

# ================== SLASH COMMAND ==================
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

    embed = discord.Embed(
        title="💳 شحن رصيد",
        description=(
            f"🆔 **ID:** `{deposit_id}`\n"
            f"💎 **النقاط:** `{points}`\n"
            f"💵 **المبلغ المطلوب:** `{amount}`\n\n"
            f"📲 **فودافون كاش:** `{VODAFONE_NUMBER}`\n"
            f"🏦 **إنستا باي:** `{INSTAPAY_NUMBER}`\n"
            f"🤖 **ProBot:** `{PROBOT_OWNER_ID}`\n\n"
            "📎 **ابعت صورة إثبات التحويل كرسالة عادية هنا**"
        ),
        color=0x3498db
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

    # حفظ الطلب مؤقتًا
    pending_deposits[str(interaction.user.id)] = {
        "deposit_id": deposit_id,
        "user_id": interaction.user.id,
        "points": points,
        "amount": amount,
        "method": "غير محدد",
        "status": "waiting_proof",
        "user_message": await interaction.original_response()
    }

# ================== IMAGE HANDLER ==================
async def handle_proof_message(message: discord.Message):

    if not message.attachments:
        return

    user_id = str(message.author.id)
    if user_id not in pending_deposits:
        return

    attachment = message.attachments[0]
    if not attachment.content_type or not attachment.content_type.startswith("image"):
        return

    info = pending_deposits[user_id]

    # حذف صورة المستخدم
    await message.delete()

    # تعديل رسالة المستخدم
    await info["user_message"].edit(
        content="⏳ **في انتظار استلام الرصيد خلال 5 دقائق**"
    )

    # إرسال الطلب لروم الأدمن
    admin_channel = message.guild.get_channel(ADMIN_ACTION_CHANNEL_ID)
    if admin_channel:
        await admin_channel.send(
            embed=build_admin_embed(info, attachment.url)
        )

    # حفظ في الملف
    data = load_data()
    data[info["deposit_id"]] = info
    save_data(data)

    # مسح من المؤقت
    del pending_deposits[user_id]
