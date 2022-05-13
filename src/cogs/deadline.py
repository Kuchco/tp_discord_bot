import asyncio
import datetime
from datetime import datetime
from discord.ext import commands
from discord import Embed


class Deadline(commands.Cog):
    loops = {}
    channel = 0

    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=['dl'], invoke_without_command=True, description="Commands for deadline")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def deadline(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), entity="deadline")

    @deadline.command(name="channel", description="Set default channel for notifications\n"
                                                  "If no channel is set, notifications will pop up in the channel where"
                                                  " a deadline was created")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def set_channel(self, ctx, channel_id):
        try:
            self.channel = self.bot.get_channel(int(channel_id))
            await ctx.send('Successfully changed the default channel for deadline notifications.')
            await self.channel.send('This channel has been set as a default channel for deadline notifications.')
        except (AttributeError, ValueError):
            self.channel = 0
            await ctx.send('Specified channel id doesn\'t exist.')
            return

        for dl in self.loops:
            self.loops[dl][0].cancel()
            date_time = datetime.strptime(self.loops[dl][1], "%d-%m-%Y %H:%M:%S")
            notif_days = self.loops[dl][2]
            self.loops[dl] = [self.bot.loop.create_task(self.alert_deadline(date_time, notif_days, dl,
                                                                            ctx if self.channel == 0 else self.channel),
                                                        name=dl),
                              self.loops[dl][1], notif_days]

    @deadline.command(name="showall", description="Show all active deadlines")
    async def deadline_showall(self, ctx):
        deadlines = list(self.loops.keys())
        embed = Embed(title="Deadlines", color=0x47E9FF)
        if not deadlines:
            embed.description = 'There are no deadlines.'
        for deadline in deadlines:
            embed.add_field(name=deadline,
                            value="{}\nDays of notifications: {}".format(self.loops.get(deadline)[1],
                                                                         ', '.join(
                                                                             map(str, self.loops.get(deadline)[2]))
                                                                         ),
                            inline=False)

        await ctx.send(embed=embed)

    @deadline.command(name="end", description="Cancel a deadline")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def deadline_end(self, ctx, deadline_name):
        if self.loops.get(deadline_name)[0]:
            self.loops.get(deadline_name)[0].cancel()
            self.loops.pop(deadline_name)
            await ctx.send('Deadline for {} has been cancelled.'.format(deadline_name))
        else:
            await ctx.send('Deadline for {} doesn\'t exist.'.format(deadline_name))

    @deadline.command(name="endall", description="Cancel all deadlines")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def deadline_end_all(self, ctx):
        for dl in self.loops:
            self.loops[dl][0].cancel()
        self.loops.clear()
        await ctx.send('All deadlines were cancelled.')

    @deadline.command(name="edit", description="Edit a deadline")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def deadline_edit(self, ctx, deadline_name, *args):
        if self.loops.get(deadline_name):
            if len(args) == 1:
                failed = await self.deadline_create(ctx, deadline_name, args[0], False, 1)
            elif len(args) == 2:
                failed = await self.deadline_create(ctx, deadline_name, args[0], args[1], 1)
            elif len(args) > 2:
                await ctx.send('Too many arguments.')
                return
            else:
                await ctx.send('Too few arguments.')
                return
            if not failed == -1:
                await ctx.send('Deadline for {} has been changed.'.format(deadline_name))
        else:
            await ctx.send('Deadline for {} doesn\'t exist.'.format(deadline_name))

    @deadline.command(name="create", description="Create a deadline\n"
                                                 "In format: '-dl create [name of deadline] [dd/mm/rr HH/MM/SS]/["
                                                 "dd/mm/rr] "
                                                 "[days of notifications](optional)'\n"
                                                 'e.g.: -dl create "Assigment 1" "1/11/21 23:59:59" "1,2,5"')
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def deadline_create(self, ctx, name, *args):
        if self.loops.get(name):
            try:
                args[2] == 1
            except IndexError:
                await ctx.send('Specified deadline name already exists. Try again with a different name.')
                return
        try:
            if len(args[0]) > 8:
                date_time = datetime.strptime(args[0], '%d/%m/%y %H:%M:%S')
            else:
                date_time = datetime.strptime(args[0], '%d/%m/%y')
                date_time = date_time.replace(hour=23, minute=59, second=59)
        except ValueError:
            await ctx.send('Wrong date format. Format must be: "dd/mm/rr HH/MM/SS" or "dd/mm/rr".')
            return -1
        except IndexError:
            await ctx.send('Too few arguments.')
            return -1
        if date_time < datetime.now():
            await ctx.send('Please enter only upcoming dates.')
            return -1

        try:
            if len(args) == 2:
                notif_days = list(map(int, args[1].split(',')))
            elif len(args) > 2:
                if args[2] == 1 and args[1]:
                    notif_days = list(map(int, args[1].split(',')))
                    self.loops.get(name)[0].cancel()
                    self.loops.pop(name)
                elif args[2] == 1 and not args[1]:
                    notif_days = [1]
                    self.loops.get(name)[0].cancel()
                    self.loops.pop(name)
                else:
                    await ctx.send('Too many arguments.')
                    return -1
            else:
                notif_days = [1]
        except ValueError:
            await ctx.send('Wrong days of notifications format. Format must be: "[number1], [number2], ...".')
            return -1

        notif_days.sort()
        await ctx.send('Deadline for {} is: {}'.format(name, date_time))
        self.loops[name] = [self.bot.loop.create_task(self.alert_deadline(date_time, notif_days, name,
                                                                          ctx if self.channel == 0 else self.channel),
                                                      name=name),
                            date_time.strftime("%d-%m-%Y %H:%M:%S"), notif_days]

    async def alert_deadline(self, input_datetime, notif_days, name, channel):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            today = datetime.now()
            if input_datetime < today:
                return

            remaining_time = input_datetime - today
            if remaining_time.days in notif_days and datetime.now().hour == 8:
                if remaining_time.days == 1:
                    await channel.send('Only 1 day remains till deadline {}.'.format(name))
                else:
                    await channel.send('There are {} days left till deadline: {}.'.format(remaining_time.days, name))

            if remaining_time.days == 0 and remaining_time.seconds <= 7200:
                self.loops.get(name)[0].cancel()
                self.loops.pop(name)
                self.loops[name] = [self.bot.loop.create_task(self.alert_deadline_last_hour(input_datetime,
                                                                                            channel,
                                                                                            name)),
                                    input_datetime.strftime("%d-%m-%Y %H:%M:%S"), notif_days]
                return

            await asyncio.sleep(3600)

    async def alert_deadline_last_hour(self, input_datetime, channel, name):
        await self.bot.wait_until_ready()
        less_than_hours = False
        while not self.bot.is_closed():
            today = datetime.now()
            remaining_time = input_datetime - today
            if remaining_time.seconds <= 3600 and not less_than_hours:
                less_than_hours = True
                await channel.send('Less than 1 hour remains till deadline: {}.'.format(name))
            if remaining_time.seconds <= 60:
                self.loops.get(name)[0].cancel()
                self.loops.pop(name)
                await channel.send('Deadline for {} has expired and was removed.'.format(name))
                return

            await asyncio.sleep(60)


def setup(bot):
    bot.add_cog(Deadline(bot))
