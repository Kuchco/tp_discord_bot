# bot.py
import os

import discord
import random
from discord.ext import commands
import logging
from dotenv import load_dotenv
import discord.emoji

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix="$",case_insensitive=True)
logging.basicConfig(level=logging.INFO)

@client.event
async def on_ready():
    guild = ""
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})\n'
    )

    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    gabot_quotes = [
        'Gabo je na kávičke v cubicone.',
        'Gabo mešká !',
        'Juro ma zastúpi',
    ]

    if message.content == 'Gabo!':
        response = random.choice(gabot_quotes)
        await message.channel.send(response)

    if message.content == "/role":
        # rol = '\n'.join([role.name for role in message.guild.roles[1:]])
        rol = [role.name for role in message.guild.roles[1:]]
        for i in range(len(rol)):
            emoji = '\N{THUMBS UP SIGN}'
            await message.channel.send(emoji + rol[i] + "\n")
            print(":kekw: " + rol[i] + "\n")


# @bot.command()
# async def roles(ctx, member):
#     """Tells you a member's roles."""
#     member = [role.name for role in member.roles[1:]]
#     await ctx.send('I see the following roles: ' + ', '.join(member))

client.run(TOKEN)
