import discord
from discord import app_commands

@app_commands.command(name="embed", description="Test embed")
async def embed(interaction: discord.Interaction):
    emb = discord.Embed(
        title="Embed Test",
        description="الإيمبيد شغال تمام ✅",
        color=0x00ff99
    )
    await interaction.response.send_message(embed=emb, ephemeral=True)
    
