import discord
from discord import app_commands
from datetime import datetime
import random
import string
import asyncio

TICKET_CATEGORY_NAME = "🎫 التذاكر"
STAFF_ROLE_ID = 1468746308780294266
BANNER_URL = "https://i.ibb.co/Tx78tZjK/63753147-7-A0-C-4965-B8-EB-CE1156433-D1-C.jpg"


# ===================== Helpers =====================

def generate_ticket_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


def has_open_ticket(guild: discord.Guild, user: discord.Member):
    for channel in guild.text_channels:
        if channel.topic and f"ticket-owner:{user.id}" in channel.topic:
            return True
    return False


# ===================== Ticket Select =====================

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="الدعم الفني", emoji="🛠"),
            discord.SelectOption(label="مشكلة إيداع", emoji="💳"),
            discord.SelectOption(label="إبلاغ", emoji="🚨"),
            discord.SelectOption(label="أخرى", emoji="📩"),
        ]

        super().__init__(
            placeholder="اختر نوع التذكرة...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        guild = interaction.guild
        user = interaction.user
        ticket_type = self.values[0]

        if has_open_ticket(guild, user):
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
            overwrites=overwrites,
            topic=f"ticket-owner:{user.id}"
        )

        timestamp = int(datetime.utcnow().timestamp())
        internal_id = generate_ticket_id()

        embed = discord.Embed(
            title="🎫 تم فتح تذكرتك بنجاح",
            description=(
                f"👤 **المستخدم:** {user.mention}\n"
                f"📌 **النوع:** `{ticket_type}`\n"
                f"🆔 **رقم التذكرة:** `{internal_id}`\n"
                f"🕒 <t:{timestamp}:F>\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📜 **شروط التذكرة:**\n"
                "• يرجى شرح المشكلة بالتفصيل.\n"
                "• يمنع السب أو الإساءة.\n"
                "• يمنع منشن الإدارة عشوائياً.\n\n"
                "✨ سيتم الرد عليك في أقرب وقت ممكن."
            ),
            color=0x00ff99
        )

        # صورة الشخص فوق يمين
        embed.set_thumbnail(url=user.display_avatar.url)

        # البانر
        embed.set_image(url=BANNER_URL)

        embed.set_footer(text="Trono Trade • Premium Support")

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


# ===================== Controls =====================

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="👑 استلام", style=discord.ButtonStyle.success)
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message(
                "❌ هذا الزر مخصص لفريق الدعم فقط.",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        await interaction.followup.send(
            f"👑 تم استلام التذكرة بواسطة {interaction.user.mention}"
        )

    @discord.ui.button(label="❌ إغلاق التذكرة", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        if STAFF_ROLE_ID not in [r.id for r in interaction.user.roles]:
            await interaction.response.send_message(
                "❌ هذا الزر مخصص لفريق الدعم فقط.",
                ephemeral=True
            )
            return

        await interaction.response.send_message("🔒 سيتم حذف التذكرة بعد 10 ثواني...")

        await asyncio.sleep(10)

        await interaction.channel.delete()


# ===================== Panel Command =====================

@app_commands.command(name="ticket-panel", description="إرسال بانل التذاكر")
async def ticket_panel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎫 مركز دعم Trono Trade",
        description="اختر نوع التذكرة من القائمة بالأسفل.",
        color=0x5865F2
    )

    await interaction.response.send_message(
        embed=embed,
        view=TicketView()
    )
