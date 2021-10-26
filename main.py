# bot.py
import os

import discord
import random
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
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
        'I just wanna die'
    ]

    if message.content == 'Gabo!':
        response = random.choice(gabot_quotes)
        await message.channel.send(response)

    if message.content == '!kill_me':
        response = "You are now dead!"
        await message.channel.send(response)

client.run(TOKEN)
