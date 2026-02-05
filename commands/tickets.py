import discord
from discord.ui import View, Button
from datetime import datetime
from config import SUPPORT_ROLE_ID, LOG_CHANNEL_ID

TICKET_CATEGORY_ID = 1291949244541960245

# ===================== UTILS =====================
async def create_transcript(channel: discord.TextChannel):
    messages = []
    async for msg in channel.history(limit=None, oldest_first=True):
        time = msg.created_at.strftime("%Y-%m-%d %H:%M")
        author = f"{msg.author} ({msg.author.id})"
        content = msg.content if msg.content else ""
        messages.append(f"[{time}] {author}: {content}")

    return "\n".join(messages) if messages else "No messages."

# ===================== TICKET PANEL =====================
class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Create Ticket", style=discord.ButtonStyle.primary)
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = interaction.user
        category = guild.get_channel(TICKET_CATEGORY_ID)

        for ch in category.channels:
            if ch.topic == str(member.id):
                return await interaction.response.send_message(
                    f"❌ لديك تكت مفتوح بالفعل: {ch.mention}", ephemeral=True
                )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(SUPPORT_ROLE_ID): discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{member.name}",
            category=category,
            topic=str(member.id),
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=(
                "مرحبًا بك 👋\n\n"
                "**من فضلك اختر نوع مشكلتك من الأزرار بالأسفل**"
            ),
            color=0x2ecc71
        )

        await channel.send(
            content=f"<@&{SUPPORT_ROLE_ID}>",
            embed=embed,
            view=IssueSelectView(member)
        )

        await interaction.response.send_message(
            f"✅ تم فتح تكتك: {channel.mention}", ephemeral=True
        )

# ===================== ISSUE SELECTION =====================
class IssueSelectView(View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user

    async def _select(self, interaction, issue):
        if interaction.user != self.user:
            return await interaction.response.send_message(
                "❌ هذا التكت ليس لك", ephemeral=True
            )

        await interaction.message.delete()

        embed = discord.Embed(
            title="✅ Ticket Created",
            description=(
                f"**نوع المشكلة:** `{issue}`\n\n"
                "🕒 سيتم الرد عليك من الدعم في أقرب وقت."
            ),
            color=0x3498db
        )

        await interaction.channel.send(
            content=f"<@&{SUPPORT_ROLE_ID}>",
            embed=embed,
            view=SupportControlsView()
        )

    @discord.ui.button(label="💰 Deposit", style=discord.ButtonStyle.secondary)
    async def deposit(self, i, b): await self._select(i, "Deposit")

    @discord.ui.button(label="📈 Trading", style=discord.ButtonStyle.secondary)
    async def trading(self, i, b): await self._select(i, "Trading")

    @discord.ui.button(label="🎖 Roles", style=discord.ButtonStyle.secondary)
    async def roles(self, i, b): await self._select(i, "Roles")

    @discord.ui.button(label="❓ Other", style=discord.ButtonStyle.secondary)
    async def other(self, i, b): await self._select(i, "Other")

# ===================== SUPPORT CONTROLS =====================
class SupportControlsView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.claimed_by = None

    @discord.ui.button(label="🟢 Take Ticket", style=discord.ButtonStyle.success)
    async def take(self, interaction: discord.Interaction, button: Button):
        if SUPPORT_ROLE_ID not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Support only", ephemeral=True)

        self.claimed_by = interaction.user
        await interaction.channel.send(f"🟢 **Ticket taken by:** {interaction.user.mention}")
        button.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="🔴 Close Ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: Button):
        if SUPPORT_ROLE_ID not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message("❌ Support only", ephemeral=True)

        channel = interaction.channel
        transcript = await create_transcript(channel)

        log = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log:
            embed = discord.Embed(
                title="📁 Ticket Closed",
                description=(
                    f"📌 Channel: `{channel.name}`\n"
                    f"👮 Closed by: {interaction.user.mention}"
                ),
                color=0xe74c3c
            )
            await log.send(embed=embed)
            await log.send(f"```{transcript[:3900]}```")

        await channel.send("⛔ سيتم حذف التكت خلال 10 ثواني")
        await discord.utils.sleep_until(datetime.utcnow())
        await channel.delete()

# ===================== MESSAGE HANDLER =====================
async def handle_ticket_message(message: discord.Message, bot):
    if message.author.bot or not message.guild:
        return

    if message.content.lower() == "ticket-panel":
        embed = discord.Embed(
            title="🎫 Support Tickets",
            description="اضغط على الزر بالأسفل لفتح تكت دعم",
            color=0x5865F2
        )
        await message.channel.send(embed=embed, view=TicketPanelView())
        await message.delete()
