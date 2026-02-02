import discord
from discord import app_commands

@app_commands.command(name="ping", description="Ping test")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong", ephemeral=True)
