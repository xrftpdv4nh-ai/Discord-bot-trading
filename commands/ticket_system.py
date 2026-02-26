import discord
from discord import app_commands
from datetime import datetime
import asyncio
import io

TICKET_CATEGORY_NAME = "🎫 التذاكر"
STAFF_ROLE_ID = 1468746308780294266
LOG_CHANNEL_NAME = "ticket-logs"

BANNER_URL = "https://i.ibb.co/Tx78tZjK/63753147-7-A0-C-4965-B8-EB-CE1156433-D1-C.jpg"


# ================= Helpers =================

async def create_transcript(channel: discord.TextChannel):
    messages = []
    async for msg in channel.history(limit=None, oldest_first=True):
        time = msg.created_at.strftime("%Y-%m-%d %H:%M")
        messages.append(f"[{time}] {msg.author}: {msg.content}")

    transcript_text = "\n".join(messages)

    buffer = io.BytesIO(transcript_text.encode("utf-8"))
    return discord.File(buffer, filename=f"{channel.name}.txt")


async def has_open_ticket(bot, user_id):
    return await bot.tickets.find_one({"user_id": user_id, "status": "open"})


# ================= Select Menu =================

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="الدعم الفني", emoji="🛠"),
            discord.SelectOption(label="مشكلة شحن", emoji="💳"),
        ]

        super().__init__(
            placeholder="اختر نوع التذكرة...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        bot = interaction.client
        guild = interaction.guild
        user = interaction.user
        ticket_type = self.values[0]

        if await has_open_ticket(bot, user.id):
            await interaction.response.send_message(
                "❌ لديك تذكرة مفتوحة بالفعل.",
                ephemeral=True
            )
            return

        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        staff_role = guild.get_role(STAFF_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )

        safe_name = user.name.lower().replace(" ", "-")

        channel = await guild.create_text_channel(
            name=f"ticket-{safe_name}",
            category=category,
            overwrites=overwrites
        )

        await bot.tickets.insert_one({
            "user_id": user.id,
            "channel_id": channel.id,
            "type": ticket_type,
            "claimed_by": None,
            "status": "open",
            "created_at": datetime.utcnow()
        })

        embed = discord.Embed(
            title="🎫 تم فتح تذكرتك",
            description=(
                f"👤 {user.mention}\n"
                f"📌 النوع: `{ticket_type}`\n\n"
                "📜 يرجى شرح المشكلة بالتفصيل."
            ),
            color=0x00ff99
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_image(url=BANNER_URL)

        await channel.send(
            content=staff_role.mention if staff_role else None,
            embed=embed,
            view=TicketControlView()
        )

        await interaction.response.send_message(
            f"✅ تم إنشاء التذكرة: {channel.mention}",
            ephemeral=True
        )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# ================= Controls =================

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="👑 استلام", style=discord.ButtonStyle.success)
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        bot = interaction.client

        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message(
                "❌ هذا الزر مخصص لفريق الدعم فقط.",
                ephemeral=True
            )
            return

        ticket = await bot.tickets.find_one({"channel_id": interaction.channel.id})

        if not ticket or ticket["claimed_by"]:
            await interaction.response.send_message(
                "❌ تم استلام التذكرة بالفعل.",
                ephemeral=True
            )
            return

        await bot.tickets.update_one(
            {"channel_id": interaction.channel.id},
            {"$set": {"claimed_by": interaction.user.id}}
        )

        new_name = f"claimed-{interaction.user.name.lower()}"
        await interaction.channel.edit(name=new_name)

        await interaction.response.send_message(
            f"👑 تم استلام التذكرة بواسطة {interaction.user.mention}"
        )

    @discord.ui.button(label="❌ إغلاق التذكرة", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        bot = interaction.client

        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message(
                "❌ هذا الزر مخصص لفريق الدعم فقط.",
                ephemeral=True
            )
            return

        ticket = await bot.tickets.find_one({"channel_id": interaction.channel.id})
        if not ticket:
            return

        await interaction.response.send_message("🔒 جاري إنشاء Transcript...")

        transcript_file = await create_transcript(interaction.channel)

        log_channel = discord.utils.get(
            interaction.guild.text_channels,
            name=LOG_CHANNEL_NAME
        )

        if log_channel:
            await log_channel.send(
                content=f"📁 Transcript | User: <@{ticket['user_id']}>",
                file=transcript_file
            )

        await bot.tickets.delete_one({"channel_id": interaction.channel.id})

        await asyncio.sleep(5)
        await interaction.channel.delete()


# ================= Panel =================

@app_commands.command(name="ticket-panel", description="إرسال بانل التذاكر")
async def ticket_panel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎫 مركز دعم Trono Trade",
        description=(
            "اختر نوع التذكرة من القائمة بالأسفل.\n\n"
            "🛠 دعم فني\n"
            "💳 مشكلة شحن\n\n"
            "⚠️ يمنع فتح تذكرة بدون سبب واضح."
        ),
        color=0x5865F2
    )

    embed.set_image(url=BANNER_URL)

    await interaction.response.send_message(
        embed=embed,
        view=TicketView()
    )

# ===================== Support Call (No Prefix) =====================

# ===================== Support Call (No Prefix + DM) =====================

async def handle_support_call(bot, message: discord.Message):

    if message.content.lower().strip() != "support":
        return

    # لازم يكون داخل تكت
    if not message.channel.name.startswith("ticket") and not message.channel.name.startswith("claimed"):
        return

    # لازم يكون عنده رول السابورت
    if STAFF_ROLE_ID not in [r.id for r in message.author.roles]:
        return

    staff_role = message.guild.get_role(STAFF_ROLE_ID)
    if not staff_role:
        return

    # 👇 رسالة داخل التكت
    await message.channel.send(
        f"🚨 {staff_role.mention}\n"
        f"تم طلب الدعم بواسطة {message.author.mention}"
    )

    # 👇 إرسال DM لكل أعضاء رول السابورت
    for member in staff_role.members:
        try:
            await member.send(
                f"🚨 تم طلب دعم في السيرفر: {message.guild.name}\n"
                f"📂 التذكرة: #{message.channel.name}\n"
                f"👤 بواسطة: {message.author}\n\n"
                f"🔗 اضغط للدخول:\n{message.channel.jump_url}"
            )
        except:
            pass  # لو قافل الخاص يتخطى

# ===================== Notify User (No Prefix) =====================

async def handle_notify_user(bot, message: discord.Message):

    if message.content.lower().strip() != "come":
        return

    # لازم يكون داخل تكت
    if not message.channel.name.startswith("ticket") and not message.channel.name.startswith("claimed"):
        return

    # لازم يكون رول السابورت
    if STAFF_ROLE_ID not in [r.id for r in message.author.roles]:
        return

    # نجيب بيانات التكت من Mongo
    ticket = await bot.tickets.find_one({"channel_id": message.channel.id})
    if not ticket:
        return

    user_id = ticket["user_id"]
    member = message.guild.get_member(user_id)

    if not member:
        return

    try:
        await member.send(
            f"📢 تم استدعائك داخل التذكرة في سيرفر **{message.guild.name}**\n\n"
            f"👑 بواسطة: {message.author}\n"
            f"📂 التذكرة: #{message.channel.name}\n\n"
            f"🔗 ادخل مباشرة:\n{message.channel.jump_url}"
        )

        await message.channel.send(
            f"✅ تم إرسال تنبيه إلى {member.mention}"
        )

    except:
        await message.channel.send(
            "❌ لم يتمكن البوت من إرسال رسالة خاصة (العضو قد يكون قافل الخاص)."
        )
