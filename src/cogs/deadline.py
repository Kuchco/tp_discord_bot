import asyncio
import datetime
from datetime import datetime

from discord.ext import commands


class Deadline(commands.Cog):
    loops = {}

    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=['dl'], invoke_without_command=True, description="Príkazy pre deadline")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def deadline(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), entity="deadline")

    @deadline.command(name="showall", description="Výpis všetkých aktívnych deadlinov")
    async def deadline_showall(self, ctx):
        deadlines = list(self.loops.keys())
        embed = discord.Embed(title="Deadlines", color=0x47E9FF)
        for deadline in deadlines:
            embed.add_field(name=deadline, value=self.loops.get(deadline)[1], inline=False)

        await ctx.send(embed=embed)

    @deadline.command(name="end", description="Zrušene deadlinu")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def deadline_end(self, ctx, deadline_name):
        if self.loops.get(deadline_name)[0]:
            self.loops.get(deadline_name)[0].cancel()
            self.loops.pop(deadline_name)
            await ctx.send('Deadline pre {} bol zrušený'.format(deadline_name))

        # for i in range(len(self.loops)):
        #     if self.loops[i].get_name() == deadline_name:
        #         print("deadline ukonceny")
        #         self.loops[i].cancel()
        #
        #     if self.loops[i].cancelled():
        #         print("task canceled")
        #
        #     if self.loops[i].done():
        #         print("task done")

    @deadline.command(name="create", description="Vytvorenie deadlinu\n"
                                                 "V tvare '-dl create [názov deadlinu] [dd/mm/rr HH/MM/SS] "
                                                 "alebo [dd/mm/rr] [dni upozornenia]'\n"
                                                 'Napr.: -dl create "Zadanie 1" "1/11/21 23:59:59" "1,2,5"')
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def deadline_create(self, ctx, name, *args):
        try:
            if len(args[0]) > 8:
                date_time = datetime.strptime(args[0], '%d/%m/%y %H:%M:%S')
            else:
                date_time = datetime.strptime(args[0], '%d/%m/%y')
                date_time = date_time.replace(hour=23, minute=59, second=59)
        except ValueError:
            await ctx.send('Bol zadaný zlý formát dátumu. Formát musí byť "dd/mm/rr HH/MM/SS" alebo "dd/mm/rr".')
            return

        if len(args) > 1:
            notif_days = list(map(int, args[1].split(',')))
        else:
            notif_days = [1]

        await ctx.send('Deadline for {} is: {}'.format(name, date_time))
        self.loops[name] = [self.bot.loop.create_task(self.alert_deadline(date_time, notif_days, name), name=name),
                            date_time.strftime("%d-%m-%Y %H:%M:%S")]

    async def alert_deadline(self, input_datetime, notif_days, name):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            channel = self.bot.get_channel(902602095302148096)

            print(input_datetime)
            today = datetime.now()
            if input_datetime < today:
                print("loop ended")
                return 1

            remaining_time = input_datetime - today
            print(notif_days)
            print(remaining_time.seconds)
            if remaining_time.days in notif_days and datetime.now().hour == 8:
                if remaining_time.days == 1:
                    await channel.send('Ostáva 1 deň do konca termínu pre {}'.format(name))
                else:
                    await channel.send('Ostávajú {} dni do konca termínu pre {}'.format(remaining_time.days, name))

            if remaining_time.days == 0 and remaining_time.seconds <= 7200:
                print("uz je ten den")
                self.loops.pop(name)
                self.loops[name] = [self.bot.loop.create_task(self.alert_deadline_last_hour(input_datetime,
                                                                                            channel,
                                                                                            name)),
                                    input_datetime.strftime("%d-%m-%Y %H:%M:%S")]
                return 1

            await asyncio.sleep(3600)

    async def alert_deadline_last_hour(self, input_datetime, channel, name):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            today = datetime.now()

            remaining_time = input_datetime - today
            if remaining_time.seconds <= 3600:
                await channel.send('Ostáva menej ako jedna hodina do konca termínu pre {}'.format(name))
                self.loops.pop(name)
                return 1

            await asyncio.sleep(60)


def setup(bot):
    bot.add_cog(Deadline(bot))
