import discord
from discord.ext import commands

from src.core.base_command import BaseCommand


class Points(BaseCommand, name="Points"):
    @commands.group(aliases=['points'], invoke_without_command=True, description="Commands for points")
    @commands.guild_only()
    async def pts(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), entity="points")

    @commands.has_guild_permissions(administrator=True)
    @pts.command(name="add", description="Add points for a student. Only administrator is able to do this.")
    @commands.guild_only()
    async def pts_add(self, ctx, user: discord.User = None, *args):
        if not user:
            await ctx.send("No user selected")
        else:
            await self.bot.point_system.upsert({"_id": user.id, "guild_id": ctx.guild.id, "points": args[0]})
            await ctx.send("Points added: {}".format(args[0]))

    @pts.command(name="show", description="Show points.")
    @commands.guild_only()
    async def pts_show(self, ctx):
        data = await self.bot.point_system.find(ctx.author.id)
        print(data)
        if data["guild_id"] == ctx.guild.id:
            await ctx.send('Points: {}'.format(data['points']))


def setup(bot):
    bot.add_cog(Points(bot))
