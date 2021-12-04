# bot.py
import asyncio
import datetime
import os

import discord
from discord.ext import commands, tasks
from datetime import datetime
from datetime import date
import random
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
# client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix='?')

# @client.event
# async def on_ready():
#     for guild in client.guilds:
#         if guild.name == GUILD:
#             break
#
#     print(
#         f'{client.user} is connected to the following guild:\n'
#         f'{guild.name}(id: {guild.id})\n'
#     )
#
#     members = '\n - '.join([member.name for member in guild.members])
#     print(f'Guild Members:\n - {members}')

# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return
#
#     brooklyn_99_quotes = [
#         'I\'m the human form of the 💯 emoji.',
#         'Bingpot!',
#         (
#             'Cool. Cool cool cool cool cool cool cool, '
#             'no doubt no doubt no doubt no doubt.'
#         ),
#     ]
#
#     if message.content == 'Gabo!':
#         response = random.choice(brooklyn_99_quotes)
#         await message.channel.send(response)

@bot.command()
async def deadline(ctx, name, datetime_str):
    date_time = datetime.strptime(datetime_str, '%d/%m/%y')
    await ctx.send('Deadline for {} is: {}'.format(name, date_time))
    bot.loop.create_task(alert_deadline(date_time))

async def alert_deadline(date):
    await bot.wait_until_ready()
    while not bot.is_closed():
        print(date)
        today = date.today()
        days = date - today
        if days.days <= 3:
            channel = bot.get_channel(902602095302148096)
            await channel.send('pisomecka bude')
            return 1
        await asyncio.sleep(32)

# client.loop.create_task(AlerteHumor())
# client.run(TOKEN)
bot.run(TOKEN)
