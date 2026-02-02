from discord.ext import commands

ADMIN_IDS = [
    802148738939748373,  # ايديك
]

class WalletAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, ctx):
        return ctx.author.id in ADMIN_IDS

    @commands.command(name="add")
    async def add_balance(self, ctx, member: commands.MemberConverter, amount: int):
        if not self.is_admin(ctx):
            return

        from commands.wallet import user_wallet

        if member.id not in user_wallet:
            user_wallet[member.id] = 0

        user_wallet[member.id] += amount
        await ctx.send(f"✅ تم إضافة `{amount}` نقطة لـ {member.mention}")

    @commands.command(name="remove")
    async def remove_balance(self, ctx, member: commands.MemberConverter, amount: int):
        if not self.is_admin(ctx):
            return

        from commands.wallet import user_wallet

        user_wallet[member.id] = max(0, user_wallet.get(member.id, 0) - amount)
        await ctx.send(f"➖ تم خصم `{amount}` نقطة من {member.mention}")

    @commands.command(name="adminhelp")
    async def admin_help(self, ctx):
        if not self.is_admin(ctx):
            return

        await ctx.send(
            "**🛠️ أوامر الأدمن:**\n"
            "`!add @user amount` ➜ إضافة نقاط\n"
            "`!remove @user amount` ➜ خصم نقاط\n"
            "`!adminhelp` ➜ عرض الأوامر"
        )
