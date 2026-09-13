import discord
from discord import app_commands
from discord.ext import commands

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="فتح تذكرة", emoji="🎫", style=discord.ButtonStyle.green, custom_id="vip_ticket_open")
    async def open_ticket(self, interaction, button):
        guild = interaction.guild
        existing = discord.utils.find(
            lambda c: isinstance(c, discord.TextChannel) and
            c.name == f"ticket-{interaction.user.id}",
            guild.text_channels
        )
        if existing:
            return await interaction.response.send_message(f"🎫 لديك تذكرة بالفعل: {existing.mention}", ephemeral=True)

        category = discord.utils.find(lambda c: isinstance(c, discord.CategoryChannel) and c.name == "🎫・SUPPORT", guild.categories)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }
        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.id}", category=category, overwrites=overwrites,
            reason=f"Ticket opened by {interaction.user}"
        )
        embed = discord.Embed(
            title="🎫 Support Ticket",
            description="اكتب مشكلتك هنا وسيقوم فريق الدعم بمساعدتك.\n\nاضغط **إغلاق التذكرة** عند الانتهاء.",
            color=discord.Color.blurple()
        )
        await channel.send(content=interaction.user.mention, embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ تم فتح تذكرتك: {channel.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="إغلاق التذكرة", emoji="🔒", style=discord.ButtonStyle.red, custom_id="vip_ticket_close")
    async def close_ticket(self, interaction, button):
        if not (interaction.user.guild_permissions.manage_channels or interaction.user.guild_permissions.manage_guild):
            return await interaction.response.send_message("❌ تحتاج صلاحية إدارة القنوات لإغلاق التذكرة.", ephemeral=True)
        await interaction.response.send_message("🔒 سيتم إغلاق التذكرة.")
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup-tickets", description="إنشاء لوحة التذاكر.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setup_tickets(self, interaction):
        category = discord.utils.find(lambda c: isinstance(c, discord.CategoryChannel) and c.name == "🎫・SUPPORT", interaction.guild.categories)
        if not category:
            category = await interaction.guild.create_category("🎫・SUPPORT")
        channel = discord.utils.find(lambda c: isinstance(c, discord.TextChannel) and c.name in ("🎫・tickets", "tickets"), category.channels)
        if not channel:
            channel = await interaction.guild.create_text_channel("🎫・tickets", category=category)
        embed = discord.Embed(
            title="🎫 مركز الدعم",
            description="محتاج مساعدة؟ اضغط الزر بالأسفل لفتح تذكرة خاصة مع فريق الدعم.",
            color=discord.Color.blurple()
        )
        await channel.send(embed=embed, view=TicketView())
        await interaction.response.send_message(f"✅ تم تجهيز التذاكر في {channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketView())
        self.bot.add_view(CloseTicketView())

async def setup(bot):
    await bot.add_cog(Tickets(bot))
