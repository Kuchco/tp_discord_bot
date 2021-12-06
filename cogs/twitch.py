import json
from datetime import datetime
from discord.ext.tasks import loop
from discord.ext import commands
import requests

with open("cogs/config.json") as config_file:
    config = json.load(config_file)

class Twitch(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.check_twitch_notifications.start()
        self.online_users = {}
        self.online_users["interes_group"] = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("Twitch Cog has been loaded\n-----")

    def get_access_token(self):
        params = {
            "client_id": config['client_id'],
            "client_secret": config['client_secret'],
            "grant_type": "client_credentials"
        }

        response = requests.post("https://id.twitch.tv/oauth2/token", params=params)
        access_token = response.json()["access_token"]
        config["access_token"] = access_token

    def check_user(self):
        #self.get_access_token()
        params = {
            "login": "INTERES_Group"
        }

        headers = {
            "Authorization": "Bearer {}".format(config["access_token"]),
            "Client-id": config["client_id"]
        }

        response = requests.get("https://api.twitch.tv/helix/users", params=params, headers=headers)
        return {entry["login"]: entry["id"] for entry in response.json()["data"]}

    def get_stream(self):
        users = self.check_user().values()
        params = {
            "user_id": users
        }

        headers = {
            "Authorization": "Bearer {}".format(config["access_token"]),
            "Client-id": config["client_id"]
        }

        response = requests.get("https://api.twitch.tv/helix/streams", params=params, headers=headers)
        return {entry["user_login"]: entry for entry in response.json()["data"]}

    def get_notification(self):
        stream = self.get_stream()
        print("stream {}".format(stream))
        print("online {}".format(self.online_users))
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
            print("online users {}".format(self.online_users))

        return notifications

    @loop(seconds=90)
    async def check_twitch_notifications(self):
        channel = self.bot.get_channel(902602095302148096)
        if not channel:
            print("No channel found")
            return

        notifications = self.get_notification()
        print("notifications {}".format(notifications))
        for notif in notifications:
            print("Almost there!")
            await channel.send("Stream od {} práve začal s názvom {}".format(notif["user_name"], notif["title"]))

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("Hello there!")

def setup(bot):
    bot.add_cog(Twitch(bot))
