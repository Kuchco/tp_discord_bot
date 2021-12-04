import discord
from discord.ext import commands
import random
import datetime


class Events(commands.Cog):

        def __init__(self, bot):
            self.bot = bot

        @commands.Cog.listener()
        async def on_ready(self):
            print("Events Cog has been loaded\n-----")

        @commands.Cog.listener()
        async def on_member_join(self, member):
            # On member joins we find a channel called general and if it exists,
            # send an embed welcoming them to our guild
            channel = discord.utils.get(member.guild.text_channels, name='recording')
            if channel:
                embed = discord.Embed(description='Vitaj na našom serveri!', color=random.choice(self.bot.color_list))
                embed.set_thumbnail(url=member.avatar_url)
                embed.set_author(name=member.name, icon_url=member.avatar_url)
                embed.set_footer(text=member.guild, icon_url=member.guild.icon_url)
                embed.timestamp = datetime.datetime.utcnow()

                await channel.send(embed=embed)

        @commands.Cog.listener()
        async def on_member_remove(self, member):
            # On member remove we find a channel called general and if it exists,
            # send an embed saying goodbye from our guild-
            channel = discord.utils.get(member.guild.text_channels, name='recording')
            if channel:
                embed = discord.Embed(description='Maj sa :(', color=random.choice(self.bot.color_list))
                embed.set_thumbnail(url=member.avatar_url)
                embed.set_author(name=member.name, icon_url=member.avatar_url)
                embed.set_footer(text=member.guild, icon_url=member.guild.icon_url)
                embed.timestamp = datetime.datetime.utcnow()

                await channel.send(embed=embed)

        @commands.Cog.listener()
        async def on_command_error(self, ctx, error):
            # Ignore these errors
            ignored = (commands.CommandNotFound, commands.UserInputError)
            if isinstance(error, ignored):
                return

            # Begin error handling
            if isinstance(error, commands.CommandOnCooldown):
                m, s = divmod(error.retry_after, 60)
                h, m = divmod(m, 60)
                if int(h) is 0 and int(m) is 0:
                    await ctx.send(f' Musite čakať {int(s)} sekund na použitie tohto prikazu!')
                elif int(h) is 0 and int(m) is not 0:
                    await ctx.send(f' Musite čakať {int(m)} minut and {int(s)} sekund na použitie tohto prikazu!')
                else:
                    await ctx.send(
                        f' Musite čakať {int(h)} hodin, {int(m)} minut and {int(s)} sekund na použitie tohto prikazu!')
            elif isinstance(error, commands.CheckFailure):
                await ctx.send("Pozor! nemáte oprávnenia.")
            raise error

def setup(bot):
    bot.add_cog(Events(bot))