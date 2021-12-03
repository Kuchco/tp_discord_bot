# Libs
import discord
from discord.ext import commands
import logging
from pathlib import Path
import json

cwd = Path(__file__).parents[0]
cwd = str(cwd)
print(f"{cwd}\n-----")

# create secret file for tokens
secret = json.load(open(cwd+'/bot_config/secrets.json'))
bot = commands.Bot(command_prefix='-', case_insensitive=True)
bot.config_token = secret['DISCORD_TOKEN']
bot.config_guild = secret['DISCORD_GUILD']
logging.basicConfig(level=logging.INFO)


@bot.event
async def on_ready():
    print(f"-----\nLogged in as: {bot.user.name} : {bot.user.id}\n-----\nMy current prefix is: -\n-----")
    await bot.change_presence(activity=discord.Game(name=f"Ahoj, ja som {bot.user.name}.\na pomôžem vám na serveri!"))

@bot.command(name='hi', aliases=['hello'])
async def _hi(ctx):
    """
    A simple command which says hi to the author.
    """
    await ctx.send(f"Hi {ctx.author.mention}!")


@bot.command()
async def echo(ctx, *, message=None):
    """
    A simple command that repeats the users input back to them.
    """
    message = message or "Prosím zadaj nejakú správu."
    await ctx.message.delete()
    await ctx.send(message)


bot.run(bot.config_token)
