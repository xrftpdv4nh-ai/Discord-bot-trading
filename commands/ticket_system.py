import discord
from discord import app_commands
from datetime import datetime
import random
import string

TICKET_CATEGORY_NAME = "🎫 Support Tickets"
STAFF_ROLE_NAME = "Support"
LOG_CHANNEL_NAME = "ticket-logs"

ANIMATED_EMOJI = "<a:trono:123456789012345678>"  # غيره بإيموجي متحرك عندك
BANNER_URL = "https://i.imgur.com/4M34hi2.png"  # حط بانر خاص بـ Trono هنا


# ===================== Helpers =====================
def generate_ticket_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


def generate_ticket_number():
    return random.randint(100, 999)


def count_open_tickets(guild: discord.Guild):
    return len([ch for ch in guild.text_channels if ch.name.startswith("ticket-")])


def count_online_staff(guild: discord.Guild):
    staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
    if not staff_role:
        return 0

    return len([m for m in staff_role.members if m.status != discord.Status.offline])


# ===================== Ticket Select =====================
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support", emoji="🛠"),
            discord.SelectOption(label="Deposit Issue", emoji="💳"),
            discord.SelectOption(label="Report", emoji="🚨"),
            discord.SelectOption(label="Other", emoji="📩"),
        ]

        super().__init__(
            placeholder="Select ticket type...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        guild = interaction.guild
        user = interaction.user
        ticket_type = self.values[0]

        # منع تكرار التذكرة
        if discord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower()}"):
            await interaction.response.send_message(
                "❌ لديك تذكرة مفتوحة بالفعل.",
                ephemeral=True
            )
            return

        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True
            )

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name.lower()}",
            category=category,
            overwrites=overwrites
        )

        ticket_number = generate_ticket_number()
        internal_id = generate_ticket_id()
        timestamp = int(datetime.utcnow().timestamp())

        embed = discord.Embed(
            title=f"<:Ticket:1476263052390174886> تذكرة #{ticket_number}",
            description=(
                f"{ANIMATED_EMOJI} **Trono Support System**\n\n"
                f"👋 مرحباً بك {user.mention}\n"
                f"تم فتح تذكرتك بنجاح.\n\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"<:Member:1476262613498204195> **فتحت بواسطة:** {user.mention}\n"
                f"<:Timer:1476263162037801061> **وقت الفتح:** <t:{timestamp}:F>\n"
                f"<:ID:1476264302577979392> **معرف التذكرة:** `{internal_id}`\n"
                f"<:Pin:1476263311443234941> **نوع التذكرة:** `{ticket_type}`\n\n"
                "<:Sparkless:1476262739444895934> يرجى شرح مشكلتك بالتفصيل.\n"
                "سيتم الرد عليك في أقرب وقت ممكن."
            ),
            color=0x2ecc71
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_image(url=BANNER_URL)
        embed.set_footer(
            text="Trono Trading System • Premium Support",
            icon_url=guild.icon.url if guild.icon else None
        )

        await channel.send(
            content=staff_role.mention if staff_role else None,
            embed=embed,
            view=TicketControlView()
        )

        await interaction.response.send_message(
            f"✅ تم إنشاء التذكرة: {channel.mention}",
            ephemeral=True
        )

        log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
        if log_channel:
            await log_channel.send(
                f"📢 New Ticket #{ticket_number} | User: {user.mention} | Channel: {channel.mention}"
            )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# ===================== Controls =====================
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="استلام", style=discord.ButtonStyle.success, emoji="👑")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        staff_role = discord.utils.get(interaction.guild.roles, name=STAFF_ROLE_NAME)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message("❌ هذا الزر مخصص لفريق الدعم.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"👑 تم استلام التذكرة بواسطة {interaction.user.mention}"
        )

    @discord.ui.button(label="إغلاق", style=discord.ButtonStyle.danger, emoji="❌")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        staff_role = discord.utils.get(interaction.guild.roles, name=STAFF_ROLE_NAME)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message("❌ هذا الزر مخصص لفريق الدعم.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 جاري إغلاق التذكرة...")
        await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
        await interaction.channel.set_permissions(interaction.guild.default_role, read_messages=False)


# ===================== Panel =====================
@app_commands.command(name="ticket-panel", description="Send premium ticket panel")
async def ticket_panel(interaction: discord.Interaction):

    guild = interaction.guild

    open_count = count_open_tickets(guild)
    online_staff = count_online_staff(guild)

    embed = discord.Embed(
        title=f"{ANIMATED_EMOJI} TRONO SUPPORT CENTER",
        description=(
            "اختر نوع التذكرة من القائمة بالأسفل.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"🎟 **التذاكر المفتوحة:** `{open_count}`\n"
            f"👨‍💻 **الدعم أونلاين:** `{online_staff}`\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ يمنع فتح تذكرة بدون سبب واضح.\n"
            "⚠️ يمنع منشن الإدارة عشوائياً.\n"
            "⚠️ سيتم إغلاق التذكرة عند الإساءة."
        ),
        color=0x5865F2
    )

    embed.set_footer(text="Trono Trading System • Premium Support")

    await interaction.response.send_message(
        embed=embed,
        view=TicketView()
    )
