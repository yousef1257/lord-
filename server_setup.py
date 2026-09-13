import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# VIP SERVER SETUP
# تجهيز السيرفر بشكل احترافي بدون حذف الموجود
# ============================================================

ROLE_DEFINITIONS = [
    ("VIP Owner", discord.Colour.gold(), True),
    ("VIP Admin", discord.Colour.red(), True),
    ("VIP Moderator", discord.Colour.blue(), True),
    ("VIP Support", discord.Colour.green(), True),
    ("VIP Member", discord.Colour.blurple(), False),
]

CATEGORY_CHANNELS = {
    "📌・INFORMATION": [
        ("📜・rules", "قوانين السيرفر"),
        ("📢・announcements", "الإعلانات الرسمية"),
        ("👋・welcome", "ترحيب الأعضاء الجدد"),
    ],
    "💬・COMMUNITY": [
        ("💬・general", "الدردشة العامة"),
        ("🤖・bot-commands", "أوامر البوت"),
    ],
    "🎫・SUPPORT": [
        ("🎫・tickets", "فتح تذاكر الدعم"),
    ],
    "🛡️・STAFF": [
        ("📋・mod-logs", "سجلات الإدارة"),
        ("🚨・security-logs", "سجلات الحماية"),
        ("🔧・staff-chat", "دردشة الإدارة"),
    ],
}

RULES_TEXT = """# 🏛️・دستور السيرفر

> **مرحبًا بك في مجتمعنا.**
> وجودك بيننا يعني احترامك للمكان والأشخاص والقواعد.

### 01・الاحترام
عامل جميع الأعضاء باحترام. يمنع السب، الإهانة، التنمر أو الاستفزاز المتعمد.

### 02・السبام
يمنع إغراق القنوات بالرسائل، المنشنات، الرموز أو المحتوى المتكرر.

### 03・الإعلانات والروابط
يمنع نشر الإعلانات أو الروابط الترويجية بدون إذن الإدارة.

### 04・الخصوصية
ممنوع نشر معلومات أو صور شخصية لأي شخص بدون موافقته.

### 05・المحتوى
يمنع إرسال أي محتوى مخالف لقواعد Discord أو قوانين السيرفر.

### 06・استغلال الثغرات
إذا وجدت مشكلة أو ثغرة، أبلغ الإدارة بدل استغلالها.

### 07・قرارات الإدارة
يلتزم الأعضاء بتعليمات الإدارة المتعلقة بتنظيم السيرفر، مع إمكانية التواصل مع الإدارة عند وجود مشكلة.

### 08・العقوبات
تختلف العقوبة حسب نوع المخالفة وتكرارها، وقد تشمل التحذير أو Timeout أو Kick أو Ban.

---

⚜️ **احترم المكان... وسيحفظ لك المكان مكانتك.**
"""


class ServerSetup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _find_role(self, guild: discord.Guild, name: str):
        return discord.utils.get(guild.roles, name=name)

    async def _get_or_create_role(
        self,
        guild: discord.Guild,
        name: str,
        colour: discord.Colour,
        hoist: bool = False,
    ):
        role = await self._find_role(guild, name)
        if role:
            return role, False

        role = await guild.create_role(
            name=name,
            colour=colour,
            hoist=hoist,
            mentionable=False,
            reason="VIP Server Setup",
        )
        return role, True

    async def _get_or_create_category(self, guild: discord.Guild, name: str):
        category = discord.utils.get(guild.categories, name=name)
        if category:
            return category, False

        category = await guild.create_category(
            name=name,
            reason="VIP Server Setup",
        )
        return category, True

    async def _get_or_create_channel(
        self,
        guild: discord.Guild,
        category: discord.CategoryChannel,
        name: str,
        topic: str,
    ):
        # Search only inside the target category.
        for channel in category.text_channels:
            if channel.name == name:
                return channel, False

        channel = await guild.create_text_channel(
            name=name,
            category=category,
            topic=topic,
            reason="VIP Server Setup",
        )
        return channel, True

    async def _send_rules_if_empty(self, channel: discord.TextChannel):
        # Do not overwrite existing messages.
        async for message in channel.history(limit=5):
            if not message.author.bot or message.embeds or message.content:
                return False

        embed = discord.Embed(
            title="🏛️・دستور السيرفر",
            description=RULES_TEXT,
            colour=discord.Colour.blurple(),
        )
        embed.set_footer(text="VIP Community • Rules")
        await channel.send(embed=embed)
        return True

    @app_commands.command(
        name="setup-server",
        description="تجهيز السيرفر بالكامل بشكل احترافي بدون حذف الموجود",
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_server(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message(
                "❌ الأمر يعمل داخل السيرفر فقط.",
                ephemeral=True,
            )

        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild

        created_roles = 0
        existing_roles = 0
        created_categories = 0
        created_channels = 0
        existing_channels = 0
        rules_posted = False

        try:
            # ----------------------------------------------------
            # 1) ROLES
            # ----------------------------------------------------
            roles = {}

            for name, colour, hoist in ROLE_DEFINITIONS:
                role, created = await self._get_or_create_role(
                    guild, name, colour, hoist
                )
                roles[name] = role

                if created:
                    created_roles += 1
                else:
                    existing_roles += 1

            # ----------------------------------------------------
            # 2) CATEGORIES + CHANNELS
            # ----------------------------------------------------
            channels = {}

            for category_name, channel_defs in CATEGORY_CHANNELS.items():
                category, created = await self._get_or_create_category(
                    guild, category_name
                )

                if created:
                    created_categories += 1

                for channel_name, topic in channel_defs:
                    channel, was_created = await self._get_or_create_channel(
                        guild,
                        category,
                        channel_name,
                        topic,
                    )

                    channels[channel_name] = channel

                    if was_created:
                        created_channels += 1
                    else:
                        existing_channels += 1

            # ----------------------------------------------------
            # 3) RULES
            # ----------------------------------------------------
            rules_channel = channels.get("📜・rules")
            if rules_channel:
                rules_posted = await self._send_rules_if_empty(rules_channel)

            # ----------------------------------------------------
            # 4) BASIC CHANNEL PERMISSIONS
            #    Staff channels are private to staff roles.
            # ----------------------------------------------------
            staff_names = {
                roles["VIP Owner"],
                roles["VIP Admin"],
                roles["VIP Moderator"],
                roles["VIP Support"],
            }

            staff_channels = {
                "📋・mod-logs",
                "🚨・security-logs",
                "🔧・staff-chat",
            }

            for channel_name in staff_channels:
                channel = channels.get(channel_name)
                if not channel:
                    continue

                overwrites = dict(channel.overwrites)

                overwrites[guild.default_role] = discord.PermissionOverwrite(
                    view_channel=False
                )

                for role in staff_names:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                    )

                await channel.edit(
                    overwrites=overwrites,
                    reason="VIP Server Setup - Staff Permissions",
                )

            # ----------------------------------------------------
            # 5) TICKET CHANNEL
            # ----------------------------------------------------
            ticket_channel = channels.get("🎫・tickets")
            if ticket_channel:
                # Keep it visible to members, but prevent normal chatting.
                overwrites = dict(ticket_channel.overwrites)
                overwrites[guild.default_role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=False,
                    add_reactions=False,
                )

                for role_name in ("VIP Owner", "VIP Admin", "VIP Moderator", "VIP Support"):
                    role = roles.get(role_name)
                    if role:
                        overwrites[role] = discord.PermissionOverwrite(
                            view_channel=True,
                            send_messages=True,
                            read_message_history=True,
                        )

                await ticket_channel.edit(
                    overwrites=overwrites,
                    reason="VIP Server Setup - Ticket Permissions",
                )

            # ----------------------------------------------------
            # 6) WELCOME CHANNEL PERMISSIONS
            # ----------------------------------------------------
            welcome_channel = channels.get("👋・welcome")
            if welcome_channel:
                overwrites = dict(welcome_channel.overwrites)
                overwrites[guild.default_role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=False,
                )
                await welcome_channel.edit(
                    overwrites=overwrites,
                    reason="VIP Server Setup - Welcome Permissions",
                )

            # ----------------------------------------------------
            # 7) FINAL REPORT
            # ----------------------------------------------------
            embed = discord.Embed(
                title="👑・VIP SERVER SETUP",
                description=(
                    "تم تجهيز البنية الأساسية للسيرفر بنجاح.\n\n"
                    "🛡️ **لم يتم حذف أي قناة أو رتبة موجودة.**\n"
                    "النظام ينشئ الناقص فقط ويعيد استخدام الموجود."
                ),
                colour=discord.Colour.gold(),
            )

            embed.add_field(
                name="🎭 الرتب",
                value=f"تم إنشاء **{created_roles}** • موجودة **{existing_roles}**",
                inline=False,
            )
            embed.add_field(
                name="📁 الأقسام",
                value=f"تم إنشاء **{created_categories}**",
                inline=True,
            )
            embed.add_field(
                name="📺 القنوات",
                value=(
                    f"تم إنشاء **{created_channels}**\n"
                    f"موجودة **{existing_channels}**"
                ),
                inline=True,
            )
            embed.add_field(
                name="📜 القوانين",
                value="تم نشرها ✅" if rules_posted else "موجودة بالفعل أو لم تُنشر",
                inline=False,
            )
            embed.set_footer(
                text=f"{guild.name} • VIP Management System"
            )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ البوت لا يملك الصلاحيات الكافية.\n"
                "تأكد أن لديه **Manage Channels + Manage Roles + View Channels + Send Messages**.",
                ephemeral=True,
            )
        except Exception as error:
            print(f"❌ setup-server error: {error}")
            await interaction.followup.send(
                f"❌ حصل خطأ أثناء التجهيز:\n`{str(error)[:1500]}`",
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerSetup(bot))
