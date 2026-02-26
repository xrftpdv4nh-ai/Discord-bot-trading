import discord
from discord import app_commands
from datetime import datetime
import random
import string

TICKET_CATEGORY_NAME = "🎫 التذاكر"
STAFF_ROLE_NAME = "Support"
LOG_CHANNEL_NAME = "ticket-logs"

ANIMATED_EMOJI = "<a:trono:123456789012345678>"
BANNER_URL = "https://i.ibb.co/Tx78tZjK/63753147-7-A0-C-4965-B8-EB-CE1156433-D1-C.jpg"


# ===================== Helpers =====================
def generate_ticket_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


def generate_ticket_number():
    return random.randint(100, 999)


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

        # منع فتح أكثر من تكت لنفس الشخص
        for channel in guild.text_channels:
            if channel.name.startswith(f"ticket-{user.id}"):
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
            name=f"ticket-{user.id}",
            category=category,
            overwrites=overwrites
        )

        ticket_number = generate_ticket_number()
        internal_id = generate_ticket_id()
        timestamp = int(datetime.utcnow().timestamp())

        embed = discord.Embed(
            title=f"🎫 التذكرة رقم #{ticket_number}",
            description=(
                f"{ANIMATED_EMOJI} **مركز دعم Trono Trade**\n\n"
                f"👋 أهلاً بك {user.mention}\n\n"
                f"🕒 <t:{timestamp}:F>\n"
                f"🆔 `{internal_id}`\n"
                f"📌 `{ticket_type}`\n\n"
                "📜 يرجى شرح مشكلتك بالتفصيل.\n"
                "✨ سيتم الرد عليك قريباً."
            ),
            color=0x00ff99
        )

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


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="👑 استلام", style=discord.ButtonStyle.success)
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        staff_role = discord.utils.get(interaction.guild.roles, name=STAFF_ROLE_NAME)

        if not staff_role or staff_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ هذا الزر مخصص لفريق الدعم فقط.",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        await interaction.followup.send(
            f"👑 تم استلام التذكرة بواسطة {interaction.user.mention}"
        )

    @discord.ui.button(label="❌ إغلاق", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        staff_role = discord.utils.get(interaction.guild.roles, name=STAFF_ROLE_NAME)

        if not staff_role or staff_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ هذا الزر مخصص لفريق الدعم فقط.",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        await interaction.channel.edit(name=f"closed-{interaction.channel.name}")
        await interaction.followup.send("🔒 تم إغلاق التذكرة.")
