from discord.ext import commands

class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='q')
    async def _quit(self, ctx):
        await self.bot.logout()