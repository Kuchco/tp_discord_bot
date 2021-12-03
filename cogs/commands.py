import discord
from discord.ext import commands
import platform

import cogs._json

class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Commands Cog has been loaded\n-----")

    @commands.command()
    async def stats(self, ctx):
        """
        A usefull command that displays bot statistics.
        """
        version_of_python = platform.python_version()
        dpy_version = discord.__version__
        server_count = len(self.bot.guilds)
        member_count = len(set(self.bot.get_all_members()))

        embed = discord.Embed(title=f'{self.bot.user.name} Stats', description='\uFEFF', colour=ctx.author.colour, timestamp=ctx.message.created_at)


        embed.add_field(name='Python Version:', value = version_of_python)
        embed.add_field(name='Discord.Py Version', value=dpy_version)
        embed.add_field(name='Total Guilds:', value=str(server_count))
        embed.add_field(name='Total Users:', value=str(member_count))

        embed.set_footer(text=f"Carpe Noctem | {self.bot.user.name}")
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        await ctx.send(embed=embed)

        @commands.command(aliases=['disconnect', 'close', 'stopbot'])
        @commands.is_owner()
        async def logout(self, ctx):
            """
            If the user running the command owns the bot then this will disconnect the bot from discord.
            """
            await ctx.send(f"Ahoj {ctx.author.mention}, odhlasujem sa :wave:")
            await self.bot.logout()


        @commands.command()
        @commands.is_owner()
        async def blacklist(self, ctx, user: discord.Member):
            if ctx.message.author.id == user.id:
                await ctx.send("Ahoj,nemôžeš seba dať na čiernu listinu!")
                return

            self.bot.blacklisted_users.append(user.id)
            data = cogs._json.read_json("blacklist")
            data["blacklistedUsers"].append(user.id)
            cogs._json.write_json(data, "blacklist")
            await ctx.send(f"Ahoj, si pridany {user.name}  na čiernej listine.")

        @commands.command()
        @commands.is_owner()
        async def unblacklist(self, ctx, user: discord.Member):
            self.bot.blacklisted_users.remove(user.id)
            data = cogs._json.read_json("blacklist")
            data["blacklistedUsers"].remove(user.id)
            cogs._json.write_json(data, "blacklist")
            await ctx.send(f"Hey, Zrušil som pre vás  {user.name} čiernu listinu.")

def setup(bot):
    bot.add_cog(Commands(bot))
