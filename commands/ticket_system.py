import discord
from discord import app_commands
from datetime import datetime

TICKET_CATEGORY_NAME = "🎫 Support Tickets"
STAFF_ROLE_NAME = "Support"
LOG_CHANNEL_NAME = "ticket-logs"

ANIMATED_EMOJI = "<a:trono:123456789012345678>"  # غيره بإيموجي متحرك عندك


# ===================== Helper =====================
def count_open_tickets(guild: discord.Guild):
    return len([
        ch for ch in guild.text_channels
        if ch.name.startswith("ticket-")
    ])


def count_online_staff(guild: discord.Guild):
    staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
    if not staff_role:
        return 0

    return len([
        m for m in staff_role.members
        if m.status != discord.Status.offline
    ])


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

        embed = discord.Embed(
            title=f"{ANIMATED_EMOJI} TRONO SUPPORT TICKET",
            description=(
                f"👤 **User:** {user.mention}\n"
                f"📌 **Type:** `{ticket_type}`\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"🕒 **Created:** <t:{int(datetime.utcnow().timestamp())}:F>\n\n"
                "📝 الرجاء شرح مشكلتك بالتفصيل."
            ),
            color=0x2ecc71
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="Trono Premium Support")

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
                f"📢 New Ticket: {channel.mention} | User: {user.mention}"
            )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


# ===================== Controls =====================
class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", style=discord.ButtonStyle.primary, emoji="👤")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        staff_role = discord.utils.get(interaction.guild.roles, name=STAFF_ROLE_NAME)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message("❌ Staff only.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"👤 Claimed by {interaction.user.mention}"
        )

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        staff_role = discord.utils.get(interaction.guild.roles, name=STAFF_ROLE_NAME)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message("❌ Staff only.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Closing ticket...")
        await interaction.channel.edit(name=f"closed-{interaction.channel.name}")


# ===================== Panel =====================
@app_commands.command(name="ticket-panel", description="Send advanced ticket panel")
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
