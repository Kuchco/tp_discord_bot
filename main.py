import json
import logging
import os
from pathlib import Path

import discord
import motor.motor_asyncio
from discord.ext import commands

from main_utils import create_bot
from utils.mongo import Document

cwd = Path(__file__).parents[0]
cwd = str(cwd)
print(f"{cwd}\n-----")

secret = json.load(open(cwd+'/bot_config/secret.json'))
GUILD = secret['DISCORD_GUILD']
logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
# noinspection PyDunderSlots,PyUnresolvedReferences
intents.members = True
client = discord.Client(intents=intents)
bot = create_bot(cwd, intents, secret)


@bot.event
async def on_ready():
    # On ready, print some details to standard out
    print(f"-----\nLogged in as: {bot.user.name} : {bot.user.id}\n-----\nMôj prefix je: {bot.default_prefix}\n-----")
    await bot.change_presence(activity=discord.Game(name=f"Ahoj, ja som {bot.user.name}.\na pomôžem vám na serveri!"))


@bot.event
@commands.has_guild_permissions(administrator=True)
async def on_message(message):
    # Ignore messages sent by yourself
    if message.author.bot or message.author.id == bot.user.id:
        return

    if message.content.startswith(f"<@!{bot.user.id}>") and len(message.content) == len(f"<@!{bot.user.id}>"):
        data = await bot.config.get_by_id(message.guild.id)
        if not data or "prefix" not in data:
            prefix = bot.default_prefix
        else:
            prefix = data["prefix"]
        await message.channel.send(f"Môj prefix na tomto serveri je  `{prefix}`", delete_after=15)

    await bot.process_commands(message)


if __name__ == '__main__':
    bot.client = client
    bot.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(bot.connection_url))
    bot.db = bot.mongo["discordBot"]
    bot.config = Document(bot.db, "config")
    bot.guild_question_channel = Document(bot.db, "guild_question_channel")
    bot.question = Document(bot.db, "question")
    bot.reaction_roles = Document(bot.db, "reaction_roles")
    bot.point_system = Document(bot.db, "point_system")
    bot.youtube = Document(bot.db, "youtube")

    # When running this file, if it is the 'main' file
    # I.E it's not being imported from another python file run this
    for file in os.listdir(cwd+"/cogs"):
        if file.endswith(".py") and not file.startswith("_"):
            bot.load_extension(f"cogs.{file[:-3]}")

    bot.run(bot.config_token)
