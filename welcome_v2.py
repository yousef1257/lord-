import sqlite3
import random
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands


DATABASE = "welcome.db"

WELCOME_MESSAGES = [
    "نورت السيرفر يا {user} ✨\nوجودك أضاف للمكان شخصًا جديدًا من عائلتنا.",
    "أهلًا وسهلًا بـ {user} 🔥\nنتمنى لك تجربة ممتعة ومميزة معنا.",
    "عضو جديد وصل! 🎉\nرحّبوا بـ {user} وخلّوه يحس إنه وسط أهله.",
    "مرحبًا بك في **{server}** يا {user} 👑\nابدأ رحلتك واقرأ القوانين قبل المشاركة.",
]


def db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_v2_database():
    connection = db()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS welcome_v2_settings (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            role_id INTEGER,
            log_channel_id INTEGER
        )
        """
    )
    connection.commit()
    connection.close()


def get_v2_settings(guild_id: int):
    connection = db()
    row = connection.execute(
        "SELECT * FROM welcome_v2_settings WHERE guild_id = ?",
        (guild_id,),
    ).fetchone()
    connection.close()
    return row


def save_v2_settings(guild_id: int, channel_id: int, role_id, log_channel_id):
    connection = db()

    # تعطيل نظام الترحيب القديم حتى لا تظهر رسالتان.
    connection.execute(
        "UPDATE welcome_settings SET enabled = 0 WHERE guild_id = ?",
        (guild_id,),
    )

    connection.execute(
        """
        INSERT INTO welcome_v2_settings
            (guild_id, channel_id, role_id, log_channel_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
            channel_id = excluded.channel_id,
            role_id = excluded.role_id,
            log_channel_id = excluded.log_channel_id
        """,
        (guild_id, channel_id, role_id, log_channel_id),
    )

    connection.commit()
    connection.close()


def rules_embed(guild: discord.Guild):
    embed = discord.Embed(
        title="📜 قوانين السيرفر",
        description=(
            f"مرحبًا بك في **{guild.name}**.\n"
            "قبل المشاركة، يرجى قراءة القوانين والالتزام بها."
        ),
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="01 • الاحترام",
        value="احترم جميع الأعضاء والإدارة. ممنوع الإهانة أو الاستفزاز أو التنمر.",
        inline=False,
    )
    embed.add_field(
        name="02 • المحتوى",
        value="ممنوع نشر أي محتوى مخالف للقوانين أو مزعج للمجتمع.",
        inline=False,
    )
    embed.add_field(
        name="03 • السبام",
        value="تجنب التكرار المزعج، المنشن الجماعي، والرسائل غير المفيدة.",
        inline=False,
    )
    embed.add_field(
        name="04 • الخصوصية",
        value="لا تنشر معلومات شخصية لك أو لغيرك ولا تحاول الحصول على بيانات الآخرين.",
        inline=False,
    )
    embed.add_field(
        name="05 • الإدارة",
        value="قرارات الإدارة تهدف لحماية السيرفر. عند وجود مشكلة استخدم الدعم.",
        inline=False,
    )
    embed.set_footer(text="VIP Welcome System • Rules")
    return embed


class WelcomeV2View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📜 القوانين",
        style=discord.ButtonStyle.secondary,
        custom_id="vip_welcome_v2_rules",
    )
    async def rules_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.send_message(
            embed=rules_embed(interaction.guild),
            ephemeral=True,
        )

    @discord.ui.button(
        label="🆘 الدعم",
        style=discord.ButtonStyle.primary,
        custom_id="vip_welcome_v2_help",
    )
    async def help_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        embed = discord.Embed(
            title="🆘 مركز المساعدة",
            description=(
                "لو محتاج مساعدة، تواصل مع فريق الإدارة أو افتح تذكرة "
                "من نظام الدعم الموجود في السيرفر."
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="VIP Welcome System")
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


class WelcomeV2(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        create_v2_database()

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            self.bot.add_view(WelcomeV2View())
        except Exception:
            pass

    async def send_welcome(self, member: discord.Member, test=False):
        settings = get_v2_settings(member.guild.id)
        if not settings:
            return False

        channel = member.guild.get_channel(settings["channel_id"])
        if not channel:
            return False

        message = random.choice(WELCOME_MESSAGES).format(
            user=member.mention,
            server=member.guild.name,
        )

        embed = discord.Embed(
            title="✨ WELCOME TO THE SERVER",
            description=message,
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow(),
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="👤 العضو",
            value=member.mention,
            inline=True,
        )
        embed.add_field(
            name="🔢 ترتيبك",
            value=f"#{member.guild.member_count}",
            inline=True,
        )
        embed.add_field(
            name="🪪 الحساب",
            value=f"<t:{int(member.created_at.timestamp())}:R>",
            inline=True,
        )

        embed.add_field(
            name="📌 ابدأ من هنا",
            value=(
                "اقرأ القوانين من الزر بالأسفل، "
                "ثم استكشف أقسام السيرفر واستمتع بوقتك."
            ),
            inline=False,
        )

        embed.set_footer(
            text=f"{member.guild.name} • VIP Welcome System"
        )

        content = f"🎊 {member.mention}"

        if test:
            content = f"🧪 اختبار الترحيب — {member.mention}"

        try:
            await channel.send(
                content=content,
                embed=embed,
                view=WelcomeV2View(),
            )
        except discord.Forbidden:
            return False
        except Exception:
            return False

        return True

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = get_v2_settings(member.guild.id)
        if not settings:
            return

        role_id = settings["role_id"]
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(
                        role,
                        reason="VIP Welcome V2 automatic role",
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

        sent = await self.send_welcome(member)

        log_channel_id = settings["log_channel_id"]
        if log_channel_id:
            log_channel = member.guild.get_channel(log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="📥 عضو جديد",
                    description=(
                        f"**العضو:** {member.mention}\n"
                        f"**ID:** `{member.id}`\n"
                        f"**العدد الحالي:** `{member.guild.member_count}`\n"
                        f"**الترحيب:** {'✅ تم الإرسال' if sent else '❌ فشل الإرسال'}"
                    ),
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow(),
                )
                embed.set_thumbnail(url=member.display_avatar.url)

                try:
                    await log_channel.send(embed=embed)
                except (discord.Forbidden, discord.HTTPException):
                    pass

    @app_commands.command(
        name="setup-welcome-v2",
        description="تفعيل نظام الترحيب الاحترافي الجديد",
    )
    @app_commands.describe(
        channel="قناة الترحيب",
        role="رتبة العضو الجديد",
        log_channel="قناة تسجيل الدخول",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_welcome_v2(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        role: discord.Role = None,
        log_channel: discord.TextChannel = None,
    ):
        create_v2_database()

        save_v2_settings(
            guild_id=interaction.guild.id,
            channel_id=channel.id,
            role_id=role.id if role else None,
            log_channel_id=log_channel.id if log_channel else None,
        )

        embed = discord.Embed(
            title="✅ تم تفعيل Welcome V2",
            description=(
                "تم تشغيل نظام الترحيب الاحترافي.\n\n"
                f"📢 القناة: {channel.mention}\n"
                f"🎭 الرتبة: {role.mention if role else 'بدون رتبة'}\n"
                f"📋 اللوج: {log_channel.mention if log_channel else 'غير مفعل'}\n\n"
                "تم تعطيل نظام الترحيب القديم تلقائيًا حتى لا تظهر رسالتان."
            ),
            color=discord.Color.green(),
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )

    @app_commands.command(
        name="test-welcome-v2",
        description="اختبار نظام الترحيب الاحترافي الجديد",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def test_welcome_v2(self, interaction: discord.Interaction):
        if not get_v2_settings(interaction.guild.id):
            await interaction.response.send_message(
                "❌ فعّل النظام أولًا باستخدام `/setup-welcome-v2`.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        sent = await self.send_welcome(interaction.user, test=True)

        if sent:
            await interaction.followup.send(
                "✅ تم إرسال اختبار الترحيب بنجاح.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "❌ البوت لم يستطع إرسال الترحيب. تأكد من صلاحيات القناة.",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeV2(bot))
