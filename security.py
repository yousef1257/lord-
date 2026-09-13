import discord
from discord import app_commands
from discord.ext import commands
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone


class Security(commands.Cog):
    """Basic server anti-spam / anti-raid protection."""

    def __init__(self, bot):
        self.bot = bot
        self.message_history = defaultdict(lambda: deque(maxlen=12))
        self.join_history = defaultdict(lambda: deque(maxlen=20))
        self.warned_users = set()

        # Default protection values.
        self.spam_limit = 6          # messages
        self.spam_window = 8         # seconds
        self.raid_limit = 5          # joins
        self.raid_window = 15        # seconds

    def _is_staff(self, member: discord.Member) -> bool:
        return (
            member.guild.owner_id == member.id
            or member.guild_permissions.administrator
            or member.guild_permissions.manage_guild
            or member.guild_permissions.manage_messages
        )

    async def _send_log(self, guild: discord.Guild, title: str, description: str):
        channel = discord.utils.find(
            lambda c: isinstance(c, discord.TextChannel)
            and c.name in ("🛡️・security-logs", "security-logs"),
            guild.text_channels,
        )
        if not channel:
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc),
        )
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @app_commands.command(
        name="security-status",
        description="عرض حالة حماية السبام والـRaid."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def security_status(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛡️ Security Status",
            description=(
                f"**Anti-Spam:** 🟢 ON\n"
                f"• الحد: `{self.spam_limit}` رسائل خلال `{self.spam_window}` ثواني\n\n"
                f"**Anti-Raid:** 🟢 ON\n"
                f"• الحد: `{self.raid_limit}` دخول خلال `{self.raid_window}` ثانية\n\n"
                "الحماية تتجاهل الإدارة ولا تقوم بحظر الأعضاء تلقائياً."
            ),
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="security-test",
        description="اختبار نظام الحماية واللوج."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def security_test(self, interaction: discord.Interaction):
        await self._send_log(
            interaction.guild,
            "🧪 Security Test",
            f"تم تشغيل اختبار الحماية بواسطة {interaction.user.mention}.",
        )
        await interaction.response.send_message(
            "✅ نظام الحماية شغال، وتم إرسال اختبار للـsecurity logs لو القناة موجودة.",
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        member = message.author
        if not isinstance(member, discord.Member):
            return

        # Don't interfere with administrators/moderators.
        if self._is_staff(member):
            return

        now = datetime.now(timezone.utc)
        history = self.message_history[(message.guild.id, member.id)]
        history.append(now)

        # Keep only messages inside the active window.
        while history and (now - history[0]).total_seconds() > self.spam_window:
            history.popleft()

        if len(history) >= self.spam_limit:
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

            # One warning per user to avoid flooding the channel.
            key = (message.guild.id, member.id)
            if key not in self.warned_users:
                self.warned_users.add(key)

                try:
                    await message.channel.send(
                        f"⚠️ {member.mention} بلاش سبام يا صاحبي. "
                        "استنى شوية قبل ما تبعت رسائل كتير.",
                        delete_after=5,
                    )
                except discord.HTTPException:
                    pass

                await self._send_log(
                    message.guild,
                    "🚨 Anti-Spam Triggered",
                    f"العضو: {member.mention}\n"
                    f"السبب: إرسال رسائل كثيرة خلال وقت قصير.",
                )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        now = datetime.now(timezone.utc)
        history = self.join_history[member.guild.id]
        history.append(now)

        while history and (now - history[0]).total_seconds() > self.raid_window:
            history.popleft()

        if len(history) >= self.raid_limit:
            await self._send_log(
                member.guild,
                "🚨 Possible Raid Detected",
                f"تم رصد `{len(history)}` عمليات دخول خلال `{self.raid_window}` ثانية.\n"
                "تم تسجيل الحدث للمراجعة. لا يتم حظر الأعضاء تلقائياً.",
            )

    @security_status.error
    @security_test.error
    async def security_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
        if isinstance(error, app_commands.MissingPermissions):
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ محتاج صلاحية **Manage Server** لاستخدام الأمر.",
                    ephemeral=True,
                )
            return

        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ حصل خطأ أثناء تنفيذ أمر الحماية.",
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(Security(bot))
