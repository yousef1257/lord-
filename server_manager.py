import discord
from discord import app_commands
from discord.ext import commands

class ServerManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="server-info", description="عرض معلومات السيرفر.")
    async def server_info(self, interaction):
        g = interaction.guild
        embed = discord.Embed(title=f"🖥️ {g.name}", color=discord.Color.blurple())
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="👥 Members", value=str(g.member_count))
        embed.add_field(name="💬 Channels", value=str(len(g.channels)))
        embed.add_field(name="🎭 Roles", value=str(len(g.roles)))
        embed.add_field(name="🆔 ID", value=f"`{g.id}`")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="slowmode", description="تفعيل Slowmode لقناة.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction, seconds: app_commands.Range[int, 0, 21600]):
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"✅ Slowmode أصبح `{seconds}` ثانية.")

    @app_commands.command(name="lock", description="قفل القناة أمام الأعضاء.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔒 تم قفل القناة.")

    @app_commands.command(name="unlock", description="فتح القناة للأعضاء.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction):
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = None
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("🔓 تم فتح القناة.")

async def setup(bot):
    await bot.add_cog(ServerManager(bot))
