import discord
from discord.ext import commands
from datetime import datetime, timezone

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild):
        return discord.utils.find(
            lambda c: isinstance(c, discord.TextChannel) and
            c.name in ("📋・mod-logs", "mod-logs"),
            guild.text_channels
        )

    async def send_log(self, guild, title, description, color=discord.Color.blurple()):
        channel = self.get_log_channel(guild)
        if not channel:
            return
        embed = discord.Embed(
            title=title, description=description, color=color,
            timestamp=datetime.now(timezone.utc)
        )
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.send_log(
            member.guild, "📤 Member Left",
            f"**العضو:** {member.mention}\n**ID:** `{member.id}`",
            discord.Color.orange()
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self.send_log(
            guild, "🔨 Member Banned",
            f"**العضو:** {user.mention if hasattr(user, 'mention') else user}\n**ID:** `{user.id}`",
            discord.Color.red()
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.send_log(
            guild, "🔓 Member Unbanned",
            f"**العضو:** {user}\n**ID:** `{user.id}`",
            discord.Color.green()
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.send_log(
            channel.guild, "📁 Channel Created",
            f"تم إنشاء: {channel.mention if hasattr(channel, 'mention') else channel.name}",
            discord.Color.green()
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.send_log(
            channel.guild, "🗑️ Channel Deleted",
            f"تم حذف القناة: `{channel.name}`",
            discord.Color.red()
        )

async def setup(bot):
    await bot.add_cog(Logs(bot))
