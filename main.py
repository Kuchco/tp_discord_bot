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

bot = commands.Bot(command_prefix="$", case_insensitive=True)
logging.basicConfig(level=logging.INFO)



client.run(TOKEN)
