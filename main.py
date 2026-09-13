import os
import io
import sqlite3
import asyncio
import traceback
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path


# ============================================================
#                    BASIC CONFIG
# ============================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN مش موجود في ملف .env"
    )


# ============================================================
#                    BOT INTENTS
# ============================================================

intents = discord.Intents.default()

# ضروري لمعرفة دخول وخروج الأعضاء
intents.members = True

# لو احتجناه مستقبلًا للأوامر النصية
intents.message_content = True


bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)


# ============================================================
#                    DATABASE
# ============================================================

DATABASE = "welcome.db"


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS welcome_settings (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            role_id INTEGER,
            enabled INTEGER DEFAULT 1,
            message TEXT,
            log_channel_id INTEGER,
            send_image INTEGER DEFAULT 1
        )
    """)

    db.commit()
    db.close()


def get_settings(guild_id: int):
    db = get_db()

    result = db.execute(
        """
        SELECT *
        FROM welcome_settings
        WHERE guild_id = ?
        """,
        (guild_id,)
    ).fetchone()

    db.close()

    return result


def save_settings(
    guild_id: int,
    channel_id: int,
    role_id: int | None,
    message: str,
    log_channel_id: int | None,
    send_image: bool
):
    db = get_db()

    db.execute(
        """
        INSERT INTO welcome_settings (
            guild_id,
            channel_id,
            role_id,
            enabled,
            message,
            log_channel_id,
            send_image
        )
        VALUES (?, ?, ?, 1, ?, ?, ?)

        ON CONFLICT(guild_id)
        DO UPDATE SET
            channel_id = excluded.channel_id,
            role_id = excluded.role_id,
            enabled = 1,
            message = excluded.message,
            log_channel_id = excluded.log_channel_id,
            send_image = excluded.send_image
        """,
        (
            guild_id,
            channel_id,
            role_id,
            message,
            log_channel_id,
            1 if send_image else 0
        )
    )

    db.commit()
    db.close()


def disable_welcome(guild_id: int):
    db = get_db()

    db.execute(
        """
        UPDATE welcome_settings
        SET enabled = 0
        WHERE guild_id = ?
        """,
        (guild_id,)
    )

    db.commit()
    db.close()


# ============================================================
#                    TEXT FORMATTER
# ============================================================

def format_welcome_message(
    message: str,
    member: discord.Member
):
    replacements = {
        "{user}": member.mention,
        "{username}": member.name,
        "{displayname}": member.display_name,
        "{server}": member.guild.name,
        "{member_count}": str(member.guild.member_count),
        "{id}": str(member.id)
    }

    for key, value in replacements.items():
        message = message.replace(key, value)

    return message


# ============================================================
#                    IMAGE HELPERS
# ============================================================

def load_font(size: int):
    possible_fonts = [
        "/system/fonts/sans-serif.ttf",
        "/system/fonts/Roboto-Regular.ttf",
        "/system/fonts/Roboto-Bold.ttf",
    ]

    for font_path in possible_fonts:
        try:
            return ImageFont.truetype(
                font_path,
                size
            )
        except Exception:
            pass

    return ImageFont.load_default()


def crop_avatar(image: Image.Image, size: int):
    image = image.convert("RGBA")

    width, height = image.size

    side = min(width, height)

    left = (width - side) // 2
    top = (height - side) // 2

    image = image.crop(
        (
            left,
            top,
            left + side,
            top + side
        )
    )

    image = image.resize(
        (size, size),
        Image.Resampling.LANCZOS
    )

    return image


def circular_image(image: Image.Image):
    size = image.size[0]

    mask = Image.new(
        "L",
        (size, size),
        0
    )

    draw = ImageDraw.Draw(mask)

    draw.ellipse(
        (0, 0, size, size),
        fill=255
    )

    result = Image.new(
        "RGBA",
        (size, size),
        (0, 0, 0, 0)
    )

    result.paste(
        image,
        (0, 0),
        mask
    )

    return result


async def download_avatar(member: discord.Member):
    try:
        data = await member.display_avatar.read()

        return Image.open(
            io.BytesIO(data)
        ).convert("RGBA")

    except Exception:
        return None


async def create_welcome_image(member: discord.Member):
    width = 1000
    height = 500

    # خلفية
    background = Image.new(
        "RGB",
        (width, height),
        (18, 18, 25)
    )

    draw = ImageDraw.Draw(background)

    # خطوط ديكورية
    draw.rectangle(
        (0, 0, width, 12),
        fill=(88, 101, 242)
    )

    draw.rectangle(
        (0, height - 12, width, height),
        fill=(88, 101, 242)
    )

    # دائرة خلفية للصورة
    draw.ellipse(
        (60, 100, 360, 400),
        fill=(35, 35, 50)
    )

    avatar = await download_avatar(member)

    if avatar:
        avatar = crop_avatar(
            avatar,
            270
        )

        avatar = circular_image(
            avatar
        )

        background.paste(
            avatar,
            (75, 115),
            avatar
        )

    # الخطوط
    title_font = load_font(64)
    name_font = load_font(45)
    normal_font = load_font(30)

    # النص
    draw.text(
        (420, 110),
        "WELCOME",
        font=title_font,
        fill=(255, 255, 255)
    )

    draw.text(
        (420, 200),
        member.display_name[:22],
        font=name_font,
        fill=(130, 140, 255)
    )

    draw.text(
        (420, 275),
        "Welcome to the server!",
        font=normal_font,
        fill=(220, 220, 225)
    )

    draw.text(
        (420, 325),
        f"Member #{member.guild.member_count}",
        font=normal_font,
        fill=(180, 180, 190)
    )

    # حفظ في الذاكرة
    output = io.BytesIO()

    background.save(
        output,
        format="PNG"
    )

    output.seek(0)

    return output


# ============================================================
#                    WELCOME BUTTONS
# ============================================================

class WelcomeView(discord.ui.View):

    def __init__(self):
        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="📜 القوانين",
        style=discord.ButtonStyle.secondary,
        custom_id="welcome_rules"
    )
    async def rules_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        embed = discord.Embed(
            title="📜 قوانين السيرفر",
            description=(
                "يرجى الالتزام بقوانين السيرفر واحترام جميع الأعضاء.\n\n"
                "1️⃣ ممنوع السب أو الإهانة.\n"
                "2️⃣ ممنوع السبام.\n"
                "3️⃣ ممنوع نشر محتوى مخالف.\n"
                "4️⃣ احترم الإدارة والأعضاء.\n"
                "5️⃣ استمتع بوقتك ❤️"
            ),
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @discord.ui.button(
        label="🆘 المساعدة",
        style=discord.ButtonStyle.primary,
        custom_id="welcome_help"
    )
    async def help_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        embed = discord.Embed(
            title="🆘 المساعدة",
            description=(
                "لو محتاج مساعدة، تواصل مع الإدارة.\n\n"
                "يمكنك أيضًا استخدام أوامر البوت المتاحة."
            ),
            color=discord.Color.blue()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# ============================================================
#                    ERROR EMBED
# ============================================================

def error_embed(title, description):
    return discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=discord.Color.red()
    )


def success_embed(title, description):
    return discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=discord.Color.green()
    )


# ============================================================
#                    READY EVENT
# ============================================================

@bot.event
async def on_ready():

    create_database()

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔥 VIP WELCOME BOT")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🤖 Bot: {bot.user}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"🌐 Servers: {len(bot.guilds)}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:

        # تسجيل الأوامر
        synced = await bot.tree.sync()

        print(
            f"✅ Slash Commands: {len(synced)}"
        )

    except Exception as error:

        print(
            f"❌ Sync Error: {error}"
        )

    # View للأزرار
    try:
        bot.add_view(
            WelcomeView()
        )
    except Exception:
        pass


# ============================================================
#                    MEMBER JOIN
# ============================================================

@bot.event
async def on_member_join(
    member: discord.Member
):

    print(
        f"👤 JOIN | {member} | {member.id}"
    )

    settings = get_settings(
        member.guild.id
    )

    if not settings:
        return

    if not settings["enabled"]:
        return

    # --------------------------------------------------------
    # ROLE
    # --------------------------------------------------------

    role_id = settings["role_id"]

    if role_id:

        role = member.guild.get_role(
            role_id
        )

        if role:

            try:

                await member.add_roles(
                    role,
                    reason="Automatic Welcome Role"
                )

                print(
                    f"🎭 Role added to {member}"
                )

            except discord.Forbidden:

                print(
                    "❌ لا توجد صلاحية لإعطاء الرتبة."
                )

            except Exception as error:

                print(
                    f"❌ Role Error: {error}"
                )

    # --------------------------------------------------------
    # CHANNEL
    # --------------------------------------------------------

    channel_id = settings["channel_id"]

    channel = member.guild.get_channel(
        channel_id
    )

    if not channel:

        print(
            "❌ Welcome channel not found."
        )

        return

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    message = settings["message"]

    if not message:

        message = (
            "🎉 أهلًا {user}!\n"
            "نورت **{server}** ❤️\n"
            "أنت العضو رقم **{member_count}**!"
        )

    message = format_welcome_message(
        message,
        member
    )

    # --------------------------------------------------------
    # EMBED
    # --------------------------------------------------------

    embed = discord.Embed(
        title="🎉 عضو جديد انضم!",
        description=message,
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.add_field(
        name="👤 العضو",
        value=member.mention,
        inline=True
    )

    embed.add_field(
        name="🔢 العدد",
        value=str(member.guild.member_count),
        inline=True
    )

    embed.set_footer(
        text=f"{member.guild.name} • Welcome System"
    )

    # --------------------------------------------------------
    # IMAGE
    # --------------------------------------------------------

    file = None

    if settings["send_image"]:

        try:

            image_data = await create_welcome_image(
                member
            )

            file = discord.File(
                image_data,
                filename="welcome.png"
            )

            embed.set_image(
                url="attachment://welcome.png"
            )

        except Exception as error:

            print(
                f"❌ Image Error: {error}"
            )

    # --------------------------------------------------------
    # SEND
    # --------------------------------------------------------

    try:

        await channel.send(
            content=f"🎊 {member.mention}",
            embed=embed,
            file=file,
            view=WelcomeView()
        )

        print(
            f"✅ Welcome sent for {member}"
        )

    except Exception as error:

        print(
            f"❌ Welcome Send Error: {error}"
        )

    # --------------------------------------------------------
    # LOG
    # --------------------------------------------------------

    log_channel_id = settings[
        "log_channel_id"
    ]

    if log_channel_id:

        log_channel = member.guild.get_channel(
            log_channel_id
        )

        if log_channel:

            log_embed = discord.Embed(
                title="📥 Member Joined",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )

            log_embed.add_field(
                name="👤 Member",
                value=f"{member.mention}\n`{member.id}`",
                inline=False
            )

            log_embed.add_field(
                name="🔢 Members",
                value=str(
                    member.guild.member_count
                )
            )

            log_embed.set_thumbnail(
                url=member.display_avatar.url
            )

            try:
                await log_channel.send(
                    embed=log_embed
                )
            except Exception:
                pass


# ============================================================
#                    MEMBER LEAVE
# ============================================================

@bot.event
async def on_member_remove(
    member: discord.Member
):

    print(
        f"📤 LEAVE | {member} | {member.id}"
    )

    settings = get_settings(
        member.guild.id
    )

    if not settings:
        return

    log_channel_id = settings[
        "log_channel_id"
    ]

    if not log_channel_id:
        return

    channel = member.guild.get_channel(
        log_channel_id
    )

    if not channel:
        return

    embed = discord.Embed(
        title="📤 عضو غادر السيرفر",
        description=(
            f"**العضو:** {member}\n"
            f"**ID:** `{member.id}`"
        ),
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )

    try:
        await channel.send(
            embed=embed
        )
    except Exception:
        pass


# ============================================================
#                    SETUP WELCOME
# ============================================================

@bot.tree.command(
    name="setup-welcome",
    description="إعداد نظام الترحيب بالكامل"
)
@app_commands.describe(
    channel="قناة الترحيب",
    role="الرتبة التي يحصل عليها العضو",
    log_channel="قناة اللوجات",
    send_image="إرسال صورة ترحيب"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def setup_welcome(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    role: discord.Role = None,
    log_channel: discord.TextChannel = None,
    send_image: bool = True
):

    # نؤكد الاستلام فورًا
    await interaction.response.defer(
        ephemeral=True
    )

    default_message = (
        "🎉 أهلًا {user}!\n"
        "نورت **{server}** ❤️\n\n"
        "أنت العضو رقم **{member_count}**.\n"
        "نتمنى لك وقتًا ممتعًا معنا! 🔥"
    )

    save_settings(
        guild_id=interaction.guild.id,
        channel_id=channel.id,
        role_id=role.id if role else None,
        message=default_message,
        log_channel_id=(
            log_channel.id
            if log_channel
            else None
        ),
        send_image=send_image
    )

    embed = success_embed(
        "تم تفعيل نظام الترحيب",
        (
            f"📢 **قناة الترحيب:** {channel.mention}\n"
            f"🎭 **الرتبة:** "
            f"{role.mention if role else 'بدون رتبة'}\n"
            f"📋 **Logs:** "
            f"{log_channel.mention if log_channel else 'غير مفعلة'}\n"
            f"🖼️ **صورة الترحيب:** "
            f"{'مفعلة ✅' if send_image else 'متوقفة ❌'}\n\n"
            "🔥 النظام جاهز لاستقبال الأعضاء."
        )
    )

    await interaction.followup.send(
        embed=embed,
        ephemeral=True
    )


# ============================================================
#                    TEST WELCOME
# ============================================================

@bot.tree.command(
    name="test-welcome",
    description="اختبار نظام الترحيب"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def test_welcome(
    interaction: discord.Interaction
):

    await interaction.response.defer(
        ephemeral=True
    )

    settings = get_settings(
        interaction.guild.id
    )

    if not settings:

        await interaction.followup.send(
            embed=error_embed(
                "النظام غير مفعل",
                "استخدم `/setup-welcome` أولًا."
            ),
            ephemeral=True
        )

        return

    channel = interaction.guild.get_channel(
        settings["channel_id"]
    )

    if not channel:

        await interaction.followup.send(
            embed=error_embed(
                "القناة غير موجودة",
                "قناة الترحيب المحفوظة غير موجودة."
            ),
            ephemeral=True
        )

        return

    member = interaction.user

    message = settings["message"]

    message = format_welcome_message(
        message,
        member
    )

    embed = discord.Embed(
        title="🧪 اختبار الترحيب",
        description=message,
        color=discord.Color.gold(),
        timestamp=datetime.utcnow()
    )

    embed.set_thumbnail(
        url=member.display_avatar.url
    )

    embed.add_field(
        name="👤 العضو",
        value=member.mention,
        inline=True
    )

    embed.add_field(
        name="🔢 العدد",
        value=str(
            interaction.guild.member_count
        ),
        inline=True
    )

    file = None

    if settings["send_image"]:

        try:

            image_data = await create_welcome_image(
                member
            )

            file = discord.File(
                image_data,
                filename="welcome_test.png"
            )

            embed.set_image(
                url="attachment://welcome_test.png"
            )

        except Exception as error:

            print(
                f"Test Image Error: {error}"
            )

    try:

        await channel.send(
            content=f"🧪 اختبار — {member.mention}",
            embed=embed,
            file=file,
            view=WelcomeView()
        )

        await interaction.followup.send(
            embed=success_embed(
                "تم الاختبار",
                f"تم إرسال رسالة الاختبار في {channel.mention}"
            ),
            ephemeral=True
        )

    except Exception as error:

        print(
            traceback.format_exc()
        )

        await interaction.followup.send(
            embed=error_embed(
                "فشل الاختبار",
                "البوت لا يستطيع إرسال الرسالة إلى القناة."
            ),
            ephemeral=True
        )


# ============================================================
#                    SHOW CONFIG
# ============================================================

@bot.tree.command(
    name="welcome-config",
    description="عرض إعدادات نظام الترحيب"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def welcome_config(
    interaction: discord.Interaction
):

    settings = get_settings(
        interaction.guild.id
    )

    if not settings:

        await interaction.response.send_message(
            embed=error_embed(
                "لا توجد إعدادات",
                "استخدم `/setup-welcome` لإعداد النظام."
            ),
            ephemeral=True
        )

        return

    channel = interaction.guild.get_channel(
        settings["channel_id"]
    )

    role = None

    if settings["role_id"]:
        role = interaction.guild.get_role(
            settings["role_id"]
        )

    log_channel = None

    if settings["log_channel_id"]:
        log_channel = interaction.guild.get_channel(
            settings["log_channel_id"]
        )

    embed = discord.Embed(
        title="⚙️ إعدادات الترحيب",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="🔘 الحالة",
        value=(
            "🟢 مفعلة"
            if settings["enabled"]
            else "🔴 متوقفة"
        ),
        inline=False
    )

    embed.add_field(
        name="📢 قناة الترحيب",
        value=(
            channel.mention
            if channel
            else "❌ غير موجودة"
        ),
        inline=True
    )

    embed.add_field(
        name="🎭 الرتبة",
        value=(
            role.mention
            if role
            else "بدون رتبة"
        ),
        inline=True
    )

    embed.add_field(
        name="📋 Logs",
        value=(
            log_channel.mention
            if log_channel
            else "غير مفعلة"
        ),
        inline=True
    )

    embed.add_field(
        name="🖼️ الصورة",
        value=(
            "مفعلة ✅"
            if settings["send_image"]
            else "متوقفة ❌"
        ),
        inline=True
    )

    embed.add_field(
        name="💬 الرسالة",
        value=(
            f"```text\n"
            f"{settings['message'][:900]}"
            f"\n```"
        ),
        inline=False
    )

    await interaction.response.send_message(
        embed=embed,
        ephemeral=True
    )


# ============================================================
#                    DISABLE
# ============================================================

@bot.tree.command(
    name="disable-welcome",
    description="إيقاف نظام الترحيب"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def disable_welcome_command(
    interaction: discord.Interaction
):

    disable_welcome(
        interaction.guild.id
    )

    await interaction.response.send_message(
        embed=success_embed(
            "تم إيقاف الترحيب",
            "تم تعطيل نظام الترحيب في هذا السيرفر."
        ),
        ephemeral=True
    )


# ============================================================
#                    PING
# ============================================================

@bot.tree.command(
    name="ping",
    description="اختبار سرعة البوت"
)
async def ping(
    interaction: discord.Interaction
):

    latency = round(
        bot.latency * 1000
    )

    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"**Latency:** `{latency}ms`",
        color=discord.Color.green()
    )

    await interaction.response.send_message(
        embed=embed
    )


# ============================================================
#                    COMMAND ERROR HANDLER
# ============================================================

async def handle_command_error(
    interaction: discord.Interaction,
    error
):

    print("━━━━━━━━ ERROR ━━━━━━━━")
    print(traceback.format_exc())
    print("━━━━━━━━━━━━━━━━━━━━━━")

    message = (
        "❌ حصل خطأ أثناء تنفيذ الأمر.\n"
        "راجع التيرمنال لمعرفة التفاصيل."
    )

    try:

        if interaction.response.is_done():

            await interaction.followup.send(
                message,
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                message,
                ephemeral=True
            )

    except Exception:

        pass


@setup_welcome.error
async def setup_welcome_error(
    interaction: discord.Interaction,
    error
):

    if isinstance(
        error,
        app_commands.errors.MissingPermissions
    ):

        await interaction.response.send_message(
            "❌ لازم تكون عندك صلاحية **Manage Server**.",
            ephemeral=True
        )

        return

    await handle_command_error(
        interaction,
        error
    )


@test_welcome.error
async def test_welcome_error(
    interaction: discord.Interaction,
    error
):

    if isinstance(
        error,
        app_commands.errors.MissingPermissions
    ):

        await interaction.response.send_message(
            "❌ لازم تكون عندك صلاحية **Manage Server**.",
            ephemeral=True
        )

        return

    await handle_command_error(
        interaction,
        error
    )


@welcome_config.error
async def welcome_config_error(
    interaction: discord.Interaction,
    error
):

    if isinstance(
        error,
        app_commands.errors.MissingPermissions
    ):

        await interaction.response.send_message(
            "❌ لازم تكون عندك صلاحية **Manage Server**.",
            ephemeral=True
        )

        return

    await handle_command_error(
        interaction,
        error
    )


@disable_welcome_command.error
async def disable_welcome_error(
    interaction: discord.Interaction,
    error
):

    if isinstance(
        error,
        app_commands.errors.MissingPermissions
    ):

        await interaction.response.send_message(
            "❌ لازم تكون عندك صلاحية **Manage Server**.",
            ephemeral=True
        )

        return

    await handle_command_error(
        interaction,
        error
    )


# ============================================================
#                    GLOBAL ERROR
# ============================================================

@bot.event
async def on_command_error(
    ctx,
    error
):

    print(
        f"Command Error: {error}"
    )


# ============================================================
#                    EXTENSION LOADER
# ============================================================

async def load_extensions():
    """تحميل كل الأنظمة الجانبية الموجودة داخل مجلد cogs."""
    cogs_dir = Path(__file__).parent / "cogs"
    cogs_dir.mkdir(exist_ok=True)

    for file in sorted(cogs_dir.glob("*.py")):
        if file.name.startswith("_"):
            continue
        extension = f"cogs.{file.stem}"
        try:
            await bot.load_extension(extension)
            print(f"🧩 Loaded: {extension}")
        except commands.ExtensionAlreadyLoaded:
            pass
        except Exception as error:
            print(f"❌ Failed to load {extension}: {error}")
            traceback.print_exc()


async def start_bot():
    create_database()
    print("🚀 Starting VIP Welcome Bot...")
    await load_extensions()
    await bot.start(TOKEN)


# ============================================================
#                    START
# ============================================================

if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped.")
