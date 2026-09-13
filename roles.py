import discord
from discord import app_commands
from discord.ext import commands

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add-role", description="إضافة رتبة لعضو.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def add_role(self, interaction, member: discord.Member, role: discord.Role):
        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message("❌ البوت لا يستطيع إدارة هذه الرتبة.", ephemeral=True)
        if role in member.roles:
            return await interaction.response.send_message("ℹ️ العضو لديه الرتبة بالفعل.", ephemeral=True)
        await member.add_roles(role, reason=f"Added by {interaction.user}")
        await interaction.response.send_message(f"✅ تمت إضافة {role.mention} إلى {member.mention}.")

    @app_commands.command(name="remove-role", description="إزالة رتبة من عضو.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def remove_role(self, interaction, member: discord.Member, role: discord.Role):
        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message("❌ البوت لا يستطيع إدارة هذه الرتبة.", ephemeral=True)
        if role not in member.roles:
            return await interaction.response.send_message("ℹ️ العضو لا يملك الرتبة.", ephemeral=True)
        await member.remove_roles(role, reason=f"Removed by {interaction.user}")
        await interaction.response.send_message(f"✅ تمت إزالة {role.mention} من {member.mention}.")

    @app_commands.command(name="role-info", description="عرض معلومات رتبة.")
    async def role_info(self, interaction, role: discord.Role):
        embed = discord.Embed(title=f"🎭 {role.name}", color=role.color)
        embed.add_field(name="ID", value=f"`{role.id}`")
        embed.add_field(name="Members", value=str(len(role.members)))
        embed.add_field(name="Position", value=str(role.position))
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Roles(bot))
