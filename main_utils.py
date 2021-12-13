import discord
import requests

from discord.ext import commands


def create_bot(cwd, intents, secret):
    default_prefix = "-"

    bot = discord.ext.commands.Bot(
        command_prefix=get_bot_prefix,
        case_insensitive=True,
        owner_id=271612318947868673,
        help_command=None,
        intents=intents,
    )

    bot.config_token = secret['DISCORD_TOKEN']
    bot.config_guild = secret['DISCORD_GUILD']
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

    return bot


async def get_bot_prefix(discord_bot, message):
    if not message.guild:
        return commands.when_mentioned_or(discord_bot.default_prefix)(discord_bot, message)

    try:
        data = await discord_bot.config.find(message.guild.id)

        # Make sure we have a usable prefix
        if not data or "prefix" not in data:
            return commands.when_mentioned_or(discord_bot.default_prefix)(discord_bot, message)
        return commands.when_mentioned_or(data["prefix"])(discord_bot, message)
    except:
        return commands.when_mentioned_or(discord_bot.default_prefix)(discord_bot, message)


async def text_channel_create_thread(self, name, minutes, message):
    token = 'Bot ' + self._state.http.token
    url = f"https://discord.com/api/v9/channels/{self.id}/messages/{message.id}/threads"
    headers = {
        "authorization": token,
        "content-type": "application/json"
    }
    data = {
        "name": name,
        "type": 11,
        "auto_archive_duration": minutes
    }

    return requests.post(url, headers=headers, json=data).json()
