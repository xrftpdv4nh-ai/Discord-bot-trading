import discord
from discord.ui import View, Button
from datetime import datetime
from config import (
    SUPPORT_ROLE_ID,
    LOG_CHANNEL_ID
)

# ===================== SETTINGS =====================
TICKET_CATEGORY_ID = 1291949244541960245

# ===================== HELPERS =====================
def has_support_role(member: discord.Member) -> bool:
    return any(role.id == SUPPORT_ROLE_ID for role in member.roles)

# ===================== TICKET PANEL VIEW =====================
class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Open Ticket", style=discord.ButtonStyle.success)
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)

        if not category:
            await interaction.response.send_message(
                "❌ Ticket category not found.",
                ephemeral=True
            )
            return

        # إنشاء روم التكت
        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                ),
                guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                ),
            }
        )

        embed = discord.Embed(
            title="🎟 Support Ticket",
            description=(
                "**Welcome to your support ticket.**\n\n"
                "Please choose the category that best describes your issue.\n"
                "Our support team will assist you as soon as possible."
            ),
            color=0x3498db
        )
        embed.set_footer(text="Trono Bot • Support System")

        await channel.send(
            content=f"{interaction.user.mention} <@&{SUPPORT_ROLE_ID}>",
            embed=embed,
            view=TicketOptionsView(interaction.user)
        )

        await interaction.response.send_message(
            f"✅ Your ticket has been created: {channel.mention}",
            ephemeral=True
        )

# ===================== TICKET OPTIONS =====================
class TicketOptionsView(View):
    def __init__(self, owner: discord.Member):
        super().__init__(timeout=None)
        self.owner = owner

    @discord.ui.button(label="💳 Deposit", style=discord.ButtonStyle.primary)
    async def deposit(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "Deposit")

    @discord.ui.button(label="📊 Trade", style=discord.ButtonStyle.secondary)
    async def trade(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "Trade")

    @discord.ui.button(label="🎭 Roles", style=discord.ButtonStyle.success)
    async def roles(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "Roles / Subscription")

    @discord.ui.button(label="❓ Other", style=discord.ButtonStyle.danger)
    async def other(self, interaction: discord.Interaction, button: Button):
        await self._select(interaction, "Other")

    async def _select(self, interaction: discord.Interaction, reason: str):
        if interaction.user != self.owner:
            await interaction.response.send_message(
                "❌ This is not your ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"✅ **Ticket Category:** `{reason}`\n"
            "Please describe your issue clearly.\n"
            "A support member will respond shortly.",
            ephemeral=False
        )

# ===================== SUPPORT CONTROLS =====================
class SupportControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🧑‍💼 Take Ticket", style=discord.ButtonStyle.primary)
    async def take(self, interaction: discord.Interaction, button: Button):
        if not has_support_role(interaction.user):
            await interaction.response.send_message(
                "❌ Support only.",
                ephemeral=True
            )
            return

        await interaction.channel.edit(
            name=f"taken-{interaction.user.name}"
        )

        await interaction.response.send_message(
            f"✅ Ticket taken by {interaction.user.mention}"
        )

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: Button):
        if not has_support_role(interaction.user):
            await interaction.response.send_message(
                "❌ Support only.",
                ephemeral=True
            )
            return

        log = interaction.client.get_channel(LOG_CHANNEL_ID)

        if log:
            await log.send(
                f"🔒 **Ticket Closed**\n"
                f"📍 Channel: `{interaction.channel.name}`\n"
                f"👮 Closed by: {interaction.user.mention}\n"
                f"📅 Time: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}`"
            )

        await interaction.response.send_message(
            "⏳ Closing ticket in 10 seconds..."
        )

        await interaction.channel.delete(delay=10)

# ===================== MESSAGE HANDLER =====================
async def handle_ticket_message(message: discord.Message, bot):
    if message.author.bot or not message.guild:
        return

    # أمر إنشاء بانل التكت
    if message.content.lower().strip() == "ticket-panel":
        if not has_support_role(message.author):
            return

        embed = discord.Embed(
            title="🎫 Support Tickets",
            description=(
                "Need help?\n"
                "Click the button below to open a support ticket.\n\n"
                "Our team is ready to assist you."
            ),
            color=0x2ecc71
        )
        embed.set_footer(text="Trono Bot • Ticket System")

        await message.channel.send(
            embed=embed,
            view=TicketPanelView()
        )

        await message.delete()
