import discord
from discord.ext import commands

from config import BOT_TOKEN

# ===================== Slash Commands =====================
from commands.ping import ping
from commands.embed import embed
from commands.trade import trade
from commands.clear import clear
from commands.wallet import wallet
from commands.deposit import deposit  # أمر الديبوزت

# ===================== Handlers =====================
from commands.deposit import handle_proof_message
from admin.wallet_admin import handle_admin_message
from commands.tickets import handle_ticket_message
# أوامر بدون prefix
from commands.roles_info import handle_roles_message   # a-role / e-role
from commands.roles_price import handle_sale_message   # a-sale / e-sale

# 🆕 أوامر إعطاء / سحب الرول
from commands.admin_role_commands import handle_admin_role_message

# متابعة صلاحية الرولات
from commands.role_subscription import check_roles_task

# ===================== Intents =====================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===================== Ready =====================
@bot.event
async def on_ready():
    print("🟢 Bot Online")

    # ❗ متلغيش أي حاجة
    bot.tree.clear_commands(guild=None)

    bot.tree.add_command(ping)
    bot.tree.add_command(embed)
    bot.tree.add_command(trade)
    bot.tree.add_command(clear)
    bot.tree.add_command(wallet)
    bot.tree.add_command(deposit)

    await bot.tree.sync()
    print("✅ Commands Synced")

    # ✅ تشغيل فحص انتهاء الرولات
    try:
        bot.loop.create_task(check_roles_task(bot))
        print("⏳ Role subscription task started")
    except Exception as e:
        print("❌ Role task error:", e)

# ===================== Messages =====================@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # 🎫 Tickets System
    try:
        await handle_ticket_message(message, bot)
    except Exception as e:
        print("❌ handle_ticket_message error:", e)

    # 1️⃣ a-role / e-role
    try:
        await handle_roles_message(message)
    except Exception as e:
        print("❌ handle_roles_message error:", e)

    # 2️⃣ a-sale / e-sale
    try:
        await handle_sale_message(message)
    except Exception as e:
        print("❌ handle_sale_message error:", e)

    # 3️⃣ إثباتات التحويل
    try:
        await handle_proof_message(message)
    except Exception as e:
        print("❌ handle_proof_message error:", e)

    # 4️⃣ أوامر الأدمن (add / remove)
    try:
        await handle_admin_message(bot, message)
    except Exception as e:
        print("❌ handle_admin_message error:", e)

    # 5️⃣ أوامر إعطاء / سحب الرول
    try:
        await handle_admin_role_message(bot, message)
    except Exception as e:
        print("❌ handle_admin_role_message error:", e)

    await bot.process_commands(message)

# ===================== Run =====================
bot.run(BOT_TOKEN)
