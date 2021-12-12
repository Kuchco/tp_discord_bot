import asyncio
import datetime

from discord.ext import commands
from datetime import datetime


class Deadline(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(description="Príkaz na nastavenie upozornení deadline termínu")
    async def deadline(self, ctx, name, *args):
        try:
            if len(args[0]) > 8:
                date_time = datetime.strptime(args[0], '%d/%m/%y %H:%M:%S')
            else:
                date_time = datetime.strptime(args[0], '%d/%m/%y')
        except ValueError:
            await ctx.send('Bol zadaný zlý formát dátumu. Formát musí byť "dd/mm/rr HH/MM/SS" alebo "dd/mm/rr".')
            return

        if len(args) > 1:
            notif_days = list(map(int, args[1].split(',')))
        else:
            notif_days = [1]

        # if len(args) > 1:
        #     date_time = datetime.strptime(args[0] + '-' + args[1], '%d/%m/%y-%H:%M:%S')
        # else:
        #     date_time = datetime.strptime(args[0], '%d/%m/%y')
        await ctx.send('Deadline for {} is: {}'.format(name, date_time))
        self.bot.loop.create_task(self.alert_deadline(date_time, notif_days, name))

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
                self.bot.loop.create_task(self.alert_deadline_last_hour(input_datetime, channel, name))
                return 1

            await asyncio.sleep(3600)

    async def alert_deadline_last_hour(self, input_datetime, channel, name):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            today = datetime.now()

            remaining_time = input_datetime - today
            if remaining_time.seconds <= 3600:
                await channel.send('Ostáva menej ako  1 hodina do konca termínu pre {}'.format(name))
                return 1

            await asyncio.sleep(60)


def setup(bot):
    bot.add_cog(Deadline(bot))
