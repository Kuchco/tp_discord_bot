from datetime import datetime

import discord
import requests
from discord.ext import commands
from discord.ext.tasks import loop

from src.utils.json_load import read_json

config = read_json("cogs")

class Twitch(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_twitch_notifications.start()
        self.online_users = {}
        self.online_users["interes_group"] = None
        self.toggle = True

    @commands.group(aliases=['tw'], invoke_without_command=True, description="Commands for twitch")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def twitch(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='twitch')

    @commands.Cog.listener()
    async def on_ready(self):
        print("Twitch Cog has been loaded\n-----")

    @twitch.command(name='toggle', description="Toggle twitch notifications")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def toggle_tw(self, ctx):
        self.toggle = not self.toggle
        if self.toggle:
            await ctx.send("Twitch notifications are now ON")
        else:
            await ctx.send("Twitch notifications are now OFF")

    @twitch.command(name='status', description="For checking if twitch notifs are ON/OFF")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def tw_status(self, ctx):
        if self.toggle:
            await ctx.send("Twitch notifications are ON")
        else:
            await ctx.send("Twitch notifications are OFF")

    def get_access_token(self):
        params = {
            "client_id": config['twitch_client_id'],
            "client_secret": config['twitch_client_secret'],
            "grant_type": "client_credentials"
        }

        response = requests.post("https://id.twitch.tv/oauth2/token", params=params)
        access_token = response.json()["access_token"]
        config["twitch_access_token"] = access_token

    def check_user(self):
        params = {
            "login": "INTERES_Group"
        }

        headers = {
            "Authorization": "Bearer {}".format(config["twitch_access_token"]),
            "Client-id": config["twitch_client_id"]
        }

        response = requests.get("https://api.twitch.tv/helix/users", params=params, headers=headers)
        try:
            if response.json()['status'] == 401:
                self.get_access_token()
        except KeyError:
            return {entry["login"]: entry["id"] for entry in response.json()["data"]}
        headers = {
            "Authorization": "Bearer {}".format(config["twitch_access_token"]),
            "Client-id": config["twitch_client_id"]
        }

        response = requests.get("https://api.twitch.tv/helix/users", params=params, headers=headers)
        return {entry["login"]: entry["id"] for entry in response.json()["data"]}

    def get_stream(self):
        users = self.check_user().values()
        params = {
            "user_id": users
        }

        headers = {
            "Authorization": "Bearer {}".format(config["twitch_access_token"]),
            "Client-id": config["twitch_client_id"]
        }

        response = requests.get("https://api.twitch.tv/helix/streams", params=params, headers=headers)
        return {entry["user_login"]: entry for entry in response.json()["data"]}

    def get_notification(self):
        stream = self.get_stream()
        notifications = []
        for user in stream:
            if user not in self.online_users:
                self.online_users[user] = datetime.utcnow()
            if user not in config["watchlist"]:
                self.online_users[user] = None
            else:
                started_at = datetime.strptime(stream[user]["started_at"], "%Y-%m-%dT%H:%M:%SZ")
                if self.online_users[user] is None or started_at > self.online_users[user]:
                    notifications.append(stream[user])
                    self.online_users[user] = started_at

        return notifications

    @loop(seconds=90)
    async def check_twitch_notifications(self):
        if self.toggle:
            print("tw here")
            guilds = self.bot.guilds
            notifications = self.get_notification()
            if not guilds:
                self.online_users["interes_group"] = None
            for notif in notifications:
                title_pars = notif['title'].split(" ")
                for guild in guilds:
                    if title_pars[0][1:-1] in guild.name or "TP" in guild.name:
                        for channel in guild.channels:
                            if title_pars[1].lower() in channel.name.lower() or "test-bot" == channel.name.lower():
                                embed = discord.Embed(
                                    title="Twitch stream notification",
                                    description="{} {}".format(title_pars[1], title_pars[2]),
                                    colour=discord.Colour.purple()
                                )
                                tmp = title_pars[4] +" "+title_pars[5]
                                embed.set_thumbnail(url=notif["thumbnail_url"].format(width=500,height=500))
                                embed.set_footer(text="The stream starts at : "+tmp)
                                await channel.send("@everyone", embed=embed)


def setup(bot):
    bot.add_cog(Twitch(bot))
