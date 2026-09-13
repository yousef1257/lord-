import discord
from discord import app_commands
from discord.ext import commands

class ConfigPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bot-panel", description="لوحة أوامر البوت.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def panel_command(self, interaction):
        embed = discord.Embed(
            title="⚙️ VIP BOT — Control Panel",
            description=(
                "استخدم أوامر البوت لإدارة السيرفر بسهولة.\n\n"
                "🛡️ `/security-status` — حالة الحماية\n"
                "🎫 `/setup-tickets` — تجهيز التذاكر\n"
                "🖥️ `/server-info` — معلومات السيرفر\n"
                "🎭 `/role-info` — معلومات رتبة\n"
                "🧹 `/clear` — حذف رسائل\n"
                "🔒 `/lock` — قفل القناة\n"
                "🔓 `/unlock` — فتح القناة\n"
                "🐌 `/slowmode` — Slowmode\n"
                "👋 `/setup-welcome-v2` — إعداد الترحيب"
            ),
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConfigPanel(bot))
