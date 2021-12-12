import json
from datetime import datetime

import discord
from discord.ext import commands
from discord.ext.tasks import loop
# Installed by google-api-python-client
# noinspection PyPackageRequirements
from googleapiclient.discovery import build

with open("cogs/yt.json") as config_file:
    config = json.load(config_file)


class Youtube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.youtube = build('youtube', 'v3', developerKey=config['api_key'])
        self.videos = {}
        self.db_videos = {}
        self.check_youtube_notifications.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Youtube Cog has been loaded\n-----")

    async def get_videos(self):
        request = self.youtube.search().list(
            part='snippet',
            channelId='UCRGOmuTb6Bdsmneu6cTNNgg',
            type='video',
            maxResults=5,
            order='date'
        )
        response = request.execute()
        tmp = {}
        for item in response['items']:
            tmp[item['snippet']['title']] = [item['snippet']['publishedAt'], item['snippet']['thumbnails']['default'],
                                             item['id']['videoId']]
        self.videos = tmp

    async def get_db_videos(self):
        tmp = await self.bot.youtube.get_all()
        if not tmp:
            print('here')
            self.db_videos = self.videos
            for vid in self.videos:
                await self.bot.youtube.insert({"_id": vid, "publishedAt": self.videos.get(vid)[0],
                                               "thumbnails": self.videos.get(vid)[1], "videoId": self.videos.get(vid)[2]
                                               })
        else:
            self.db_videos = tmp

    async def update_db(self):
        for vid in self.db_videos:
            await self.bot.youtube.delete(vid['_id'])
        for video in self.videos:
            await self.bot.youtube.insert({"_id": video, "publishedAt": self.videos.get(video)[0],
                                           "thumbnails": self.videos.get(video)[1], "videoId": self.videos.get(video)[2]
                                           })

    @loop(seconds=90)
    async def check_youtube_notifications(self):
        guilds = self.bot.guilds
        count = 0
        if guilds:
            await self.get_videos()
            if not self.db_videos:
                await self.get_db_videos()
            tmp_db_vid = []
            for db_vid in self.db_videos:
                tmp_db_vid.append(db_vid['_id'])
            for video in self.videos:
                if video not in tmp_db_vid:
                    count += 1
                    spit_title = video.split(' ')
                    for guild in guilds:
                        if 'TP' in guild.name:  # spit_title[0][1:] in guild.name or
                            for channel in guild.channels:
                                if spit_title[2][:-1].lower() in channel.name.lower() or 'test-bot' == channel.name.lower():
                                    embed = discord.Embed(
                                        title="Youtube upozornenie na upload videa",
                                        description="{}".format(video),
                                        colour=discord.Colour.red()
                                    )
                                    thumb_url = self.videos.get(video)[1]
                                    foot = self.videos.get(video)[0]
                                    vid_id = self.videos.get(video)[2]
                                    foot = datetime.strptime(foot, "%Y-%m-%dT%H:%M:%SZ")
                                    embed.set_thumbnail(url=thumb_url['url'])
                                    embed.add_field(name='URL', value="https://youtube.com/watch?v={}".format(vid_id))
                                    embed.set_footer(text="Video nahraté : {}".format(foot))
                                    await channel.send(embed=embed)
            if count != 0:
                await self.update_db()


def setup(bot):
    bot.add_cog(Youtube(bot))
