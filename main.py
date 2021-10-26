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
async def on_message(message):
    if message.author == client.user:
        return
    if message.content == "/role":
        rol = '\n'.join([role.name for role in message.guild.roles])
        # await message.channel.send(rol)
        print(rol)


client.run(TOKEN)
