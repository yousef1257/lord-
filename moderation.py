import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta


class Moderation(commands.Cog):
    """أوامر الإدارة الأساسية بدون لمس نظام الترحيب."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _can_act(self, interaction: discord.Interaction, member: discord.Member):
        guild = interaction.guild
        me = guild.me

        if member == interaction.user:
            return False, "❌ مينفعش تستخدم الأمر على نفسك."
        if member == guild.owner:
            return False, "❌ مينفعش تستخدم الأمر على مالك السيرفر."
        if member == me:
            return False, "❌ مينفعش تستخدم الأمر على البوت نفسه."
        if me and member.top_role >= me.top_role:
            return False, "❌ رتبة العضو أعلى من رتبة البوت أو مساوية لها."
        if isinstance(interaction.user, discord.Member) and member.top_role >= interaction.user.top_role:
            return False, "❌ مينفعش تعاقب عضو رتبته أعلى منك أو مساوية لرتبتك."
        return True, None

    @app_commands.command(name="ban", description="حظر عضو من السيرفر")
    @app_commands.describe(member="العضو", reason="سبب الحظر")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
        await interaction.response.defer(ephemeral=True)
        ok, error = await self._can_act(interaction, member)
        if not ok:
            return await interaction.followup.send(error, ephemeral=True)
        try:
            await member.ban(reason=reason[:512])
            embed = discord.Embed(title="🔨 تم حظر العضو", color=discord.Color.red())
            embed.add_field(name="العضو", value=f"{member.mention} (`{member.id}`)", inline=False)
            embed.add_field(name="بواسطة", value=interaction.user.mention)
            embed.add_field(name="السبب", value=reason[:1024], inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ البوت لا يمتلك صلاحية Ban أو أن ترتيب الرتب يمنع العملية.", ephemeral=True)

    @app_commands.command(name="kick", description="طرد عضو من السيرفر")
    @app_commands.describe(member="العضو", reason="سبب الطرد")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
        await interaction.response.defer(ephemeral=True)
        ok, error = await self._can_act(interaction, member)
        if not ok:
            return await interaction.followup.send(error, ephemeral=True)
        try:
            await member.kick(reason=reason[:512])
            embed = discord.Embed(title="👢 تم طرد العضو", color=discord.Color.orange())
            embed.add_field(name="العضو", value=f"{member.mention} (`{member.id}`)", inline=False)
            embed.add_field(name="بواسطة", value=interaction.user.mention)
            embed.add_field(name="السبب", value=reason[:1024], inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ البوت لا يمتلك صلاحية Kick أو أن ترتيب الرتب يمنع العملية.", ephemeral=True)

    @app_commands.command(name="timeout", description="إعطاء عضو Timeout")
    @app_commands.describe(member="العضو", minutes="المدة بالدقائق", reason="السبب")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: app_commands.Range[int, 1, 40320], reason: str = "بدون سبب"):
        await interaction.response.defer(ephemeral=True)
        ok, error = await self._can_act(interaction, member)
        if not ok:
            return await interaction.followup.send(error, ephemeral=True)
        try:
            await member.timeout(timedelta(minutes=minutes), reason=reason[:512])
            embed = discord.Embed(title="⏱️ تم إعطاء Timeout", color=discord.Color.gold())
            embed.add_field(name="العضو", value=member.mention, inline=False)
            embed.add_field(name="المدة", value=f"{minutes} دقيقة")
            embed.add_field(name="بواسطة", value=interaction.user.mention)
            embed.add_field(name="السبب", value=reason[:1024], inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ البوت لا يمتلك صلاحية Timeout أو أن ترتيب الرتب يمنع العملية.", ephemeral=True)

    @app_commands.command(name="untimeout", description="إزالة Timeout من عضو")
    @app_commands.describe(member="العضو", reason="السبب")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member, reason: str = "بدون سبب"):
        await interaction.response.defer(ephemeral=True)
        ok, error = await self._can_act(interaction, member)
        if not ok:
            return await interaction.followup.send(error, ephemeral=True)
        try:
            await member.timeout(None, reason=reason[:512])
            await interaction.followup.send(f"✅ تم إزالة الـTimeout من {member.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ البوت لا يمتلك الصلاحية.", ephemeral=True)

    @app_commands.command(name="clear", description="حذف من 1 إلى 100 رسالة")
    @app_commands.describe(amount="عدد الرسائل")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]):
        await interaction.response.defer(ephemeral=True)
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.followup.send("❌ الأمر متاح داخل القنوات النصية فقط.", ephemeral=True)
        try:
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"🧹 تم حذف **{len(deleted)}** رسالة.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ البوت لا يمتلك صلاحية Manage Messages.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
