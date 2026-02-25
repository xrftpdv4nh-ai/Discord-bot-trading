import discord
from discord import app_commands
from config import ADMIN_IDS
from bson import ObjectId


# ===================== دالة تحقق الأدمن =====================
def is_authorized(interaction: discord.Interaction) -> bool:
    return (
        interaction.user.id in ADMIN_IDS
        or interaction.user.guild_permissions.administrator
        or interaction.user.id == interaction.guild.owner_id
    )


# ===================== عرض العمليات المعلقة =====================
@app_commands.command(name="pending", description="عرض الإيداعات المعلقة (أدمن فقط)")
async def admin_pending(interaction: discord.Interaction):

    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ هذا الأمر مخصص للأدمن فقط.",
            ephemeral=True
        )
        return

    pending_list = await interaction.client.pending.find({
        "status": "waiting_transfer"
    }).to_list(length=25)

    if not pending_list:
        await interaction.response.send_message("✅ لا توجد عمليات معلقة.")
        return

    embed = discord.Embed(
        title="📦 العمليات المعلقة",
        color=0xe67e22
    )

    for item in pending_list:
        embed.add_field(
            name=f"ID: {item['_id']}",
            value=(
                f"👤 <@{item['user_id']}>\n"
                f"💎 {item['points']} نقطة\n"
                f"💳 المطلوب تحويله: {item.get('total_required', 'غير محدد')}"
            ),
            inline=False
        )

    await interaction.response.send_message(embed=embed)


# ===================== حذف عملية معلقة =====================
@app_commands.command(name="delete_pending", description="حذف عملية معلقة (أدمن فقط)")
@app_commands.describe(deposit_id="ID العملية")
async def delete_pending(interaction: discord.Interaction, deposit_id: str):

    if not is_authorized(interaction):
        await interaction.response.send_message(
            "❌ هذا الأمر مخصص للأدمن فقط.",
            ephemeral=True
        )
        return

    try:
        result = await interaction.client.pending.delete_one({
            "_id": ObjectId(deposit_id)
        })

        if result.deleted_count:
            await interaction.response.send_message("✅ تم حذف العملية بنجاح.")
        else:
            await interaction.response.send_message("❌ لم يتم العثور على العملية.")

    except Exception:
        await interaction.response.send_message("❌ ID غير صالح.")
