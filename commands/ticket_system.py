import discord
from discord.ui import View, Select, Button
from discord import app_commands
from config import SUPPORT_ROLE_ID, TICKET_CATEGORY_ID, TICKET_LOG_CHANNEL_ID

class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Support", description="Technical support", emoji="🛠"),
            discord.SelectOption(label="Deposit Issue", description="Deposit problem", emoji="💳"),
            discord.SelectOption(label="Report", description="Report a user", emoji="🚨"),
            discord.SelectOption(label="Other", description="Other issue", emoji="📩"),
        ]

        super().__init__(
            placeholder="Select ticket type...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select"
        )

    async def callback(self, interaction: discord.Interaction):

        guild = interaction.guild
        user = interaction.user

        # منع فتح أكثر من تكت
        existing = discord.utils.get(guild.text_channels, name=f"ticket-{user.id}")
        if existing:
            await interaction.response.send_message("❌ You already have an open ticket.", ephemeral=True)
            return

        category = guild.get_channel(TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎟 Ticket Created",
            description=f"Support will assist you shortly.\n\nType: **{self.values[0]}**",
            color=0x2ecc71
        )

        await channel.send(content=f"{user.mention}", embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)


class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):

        await interaction.response.send_message("🔒 Ticket closing in 5 seconds...")
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=5))
        await interaction.channel.delete()


# Slash command to send panel
@app_commands.command(name="ticket-panel", description="Send ticket panel")
async def ticket_panel(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🎟 TRONO SUPPORT CENTER",
        description="Select ticket type below.",
        color=0x3498db
    )

    await interaction.response.send_message(embed=embed, view=TicketView())
