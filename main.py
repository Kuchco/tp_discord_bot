# Libs

import os
import discord
from discord.ext import commands
import logging
from pathlib import Path
import json
import motor.motor_asyncio
from utils.mongo import Document

cwd = Path(__file__).parents[0]
cwd = str(cwd)
print(f"{cwd}\n-----")

async def get_prefix(bot, message):
    # If dm's
    if not message.guild:
        return commands.when_mentioned_or(bot.default_prefix)(bot, message)

    try:
        data = await bot.config.find(message.guild.id)

        # Make sure we have a useable prefix
        if not data or "prefix" not in data:
            return commands.when_mentioned_or(bot.default_prefix)(bot, message)
        return commands.when_mentioned_or(data["prefix"])(bot, message)
    except:
        return commands.when_mentioned_or(bot.default_prefix)(bot, message)


default_prefix = "-"
secret = json.load(open(cwd+'/bot_config/secret.json'))

GUILD = secret['DISCORD_GUILD']
logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
bot = commands.Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    owner_id=271612318947868673,
    help_command=None,
    intents=intents,
)
bot.config_token = secret["DISCORD_TOKEN"]
bot.config_guild = secret["DISCORD_GUILD"]
bot.connection_url = secret["mongo"]


bot.default_prefix = default_prefix


bot.colors = {
  'WHITE': 0xFFFFFF,
  'AQUA': 0x1ABC9C,
  'GREEN': 0x2ECC71,
  'BLUE': 0x3498DB,
  'PURPLE': 0x9B59B6,
  'LUMINOUS_VIVID_PINK': 0xE91E63,
  'GOLD': 0xF1C40F,
  'ORANGE': 0xE67E22,
  'RED': 0xE74C3C,
  'NAVY': 0x34495E,
  'DARK_AQUA': 0x11806A,
  'DARK_GREEN': 0x1F8B4C,
  'DARK_BLUE': 0x206694,
  'DARK_PURPLE': 0x71368A,
  'DARK_VIVID_PINK': 0xAD1457,
  'DARK_GOLD': 0xC27C0E,
  'DARK_ORANGE': 0xA84300,
  'DARK_RED': 0x992D22,
  'DARK_NAVY': 0x2C3E50
}
bot.color_list = [c for c in bot.colors.values()]
bot.cwd = cwd

@bot.event
async def on_ready():
    # On ready, print some details to standard out
    print(
        f"-----\nLogged in as: {bot.user.name} : {bot.user.id}\n-----\nMy current prefix is: {bot.default_prefix}\n-----"
    )
    await bot.change_presence(activity=discord.Game(name=f"Ahoj, ja som {bot.user.name}.\na pomôžem vám na serveri!"))

    for document in await bot.config.get_all():
        print(document)


    print("Initialized Database\n-----")


@bot.event
async def on_message(message):
    # Ignore messages sent by yourself
    if message.author.id == bot.user.id:
        return

        # Ignore messages sent by yourself
    if message.author.bot:
        return

    if message.content.startswith(f"<@!{bot.user.id}>") and len(message.content) == len(
            f"<@!{bot.user.id}>"
    ):
        data = await bot.config.get_by_id(message.guild.id)
        if not data or "prefix" not in data:
            prefix = bot.default_prefix
        else:
            prefix = data["prefix"]
        await message.channel.send(f"My prefix here is `{prefix}`", delete_after=15)



    await bot.process_commands(message)



if __name__ == '__main__':
    bot.mongo = motor.motor_asyncio.AsyncIOMotorClient(str(bot.connection_url))
    bot.db = bot.mongo["discordBot"]
    bot.config = Document(bot.db, "config")
    bot.reaction_roles = Document(bot.db, "reaction_roles")
    bot.point_system = Document(bot.db, "point_system")
    # When running this file, if it is the 'main' file
    # I.E its not being imported from another python file run this
    for file in os.listdir(cwd+"/cogs"):
        if file.endswith(".py") and not file.startswith("_"):
            bot.load_extension(f"cogs.{file[:-3]}")
    bot.run(bot.config_token)


