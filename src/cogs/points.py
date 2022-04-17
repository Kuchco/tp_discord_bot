import discord

from discord.ext import commands

from src.core.base_command import BaseCommand


class Points(BaseCommand, name="Points"):
    @commands.group(aliases=['points'], invoke_without_command=True)
    @commands.guild_only()
    async def pts(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), entity="points")

    @commands.has_role('test')
    @pts.command(name="add")
    @commands.guild_only()
    async def pts_add(self, ctx, user: discord.User = None, *args):
        if not user:
            await ctx.send("No user selected")
        else:
            await ctx.send("Hello {}".format(user))

            await self.bot.point_system.upsert({"_id": user.id, "guild_id": ctx.guild.id, "points": args[0]})
            await ctx.send("Points added: {}".format(args[0]))

    @pts.command(name="show")
    @commands.guild_only()
    async def pts_show(self, ctx):
        data = await self.bot.point_system.find(ctx.author.id)
        print(data)
        if data["guild_id"] == ctx.guild.id:
            await ctx.send('Body: {}'.format(data['points']))


def setup(bot):
    bot.add_cog(Points(bot))
