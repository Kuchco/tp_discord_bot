from discord.ext import commands

from core.base_command import BaseCommand

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.__class__.__name__} Cog has been loaded\n-----")

    # @commands.command(
    #     name="prefix",
    #     aliases=["changeprefix", "setprefix"],
    #     description="Zmena prefixu pre Gabota na tomto serveri!",
    #     usage="[prefix]",
    # )
    # @commands.has_guild_permissions(manage_guild=True)
    # async def prefix(self, ctx, *, prefix="py."):
    #     await self.bot.config.upsert({"_id": ctx.guild.id, "prefix": prefix})
    #     await ctx.send(
    #         f"Prefix bol nastavený na  `{prefix}`. Použite  `{prefix}prefix [prefix]` na zmenenie znovu!"
    #     )
    #
    # @commands.command(name="delete_prefix", aliases=["dp"], description="Vymazať prefixy !")
    # @commands.guild_only()
    # @commands.has_guild_permissions(administrator=True)
    # async def delete_prefix(self, ctx):
    #     await self.bot.config.unset({"_id": ctx.guild.id, "prefix": 1})
    #     await ctx.send("prefix bol zmenený na defaultný na tomto serveri")


def setup(bot):
    bot.add_cog(Config(bot))
