from datetime import datetime

import discord
from discord.ext.tasks import loop
from googleapiclient.discovery import build
from discord.ext import commands

from src.utils.json_load import read_json

config = read_json("cogs")

class Youtube(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.youtube = build('youtube', 'v3', developerKey=config['youtube_api_key'])
        self.videos = {}
        self.db_videos = {}
        self.check_youtube_notifications.start()
        self.toggle = True

    @commands.group(aliases=['yt'], invoke_without_command=True, description="Commands for youtube")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def youtube(self, ctx):
        await ctx.invoke(self.bot.get_command('help'), entity='youtube')

    @commands.Cog.listener()
    async def on_ready(self):
        print("Youtube Cog has been loaded\n-----")

    @youtube.command(name='toggle', description="Toggle youtube notifications")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def toggle_yt(self, ctx):
        self.toggle = not self.toggle
        if self.toggle:
            await ctx.send("Youtube notifications are now ON")
        else:
            await ctx.send("Youtube notifications are now OFF")

    @youtube.command(name='status', description="For checking if youtube notifs are ON/OFF")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def yt_status(self, ctx):
        if self.toggle:
            await ctx.send("Youtube notifications are ON")
        else:
            await ctx.send("Youtube notifications are OFF")

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
            for vid in self.videos:
                await self.bot.youtube.insert({"_id": vid, "publishedAt": self.videos.get(vid)[0],
                                               "thumbnails": self.videos.get(vid)[1], "videoId": self.videos.get(vid)[2]
                                               })
        else:
            self.db_videos = tmp

    async def update_db(self):
        db_clear = await self.bot.youtube.get_all()
        for vid in db_clear:
            await self.bot.youtube.delete(vid['_id'])
        for video in self.videos:
            await self.bot.youtube.upsert({"_id": video, "publishedAt": self.videos.get(video)[0],
                                           "thumbnails": self.videos.get(video)[1], "videoId": self.videos.get(video)[2]
                                           })

    @loop(seconds=180)
    async def check_youtube_notifications(self):
        guilds = self.bot.guilds
        if guilds and self.toggle:
            print("yt here")
            await self.get_videos()
            await self.get_db_videos()
            tmp_db_vid = []
            for db_vid in self.db_videos:
                tmp_db_vid.append(db_vid['_id'])
            count = 0
            for video in self.videos:
                if video not in tmp_db_vid:
                    count += 1
                    split_title = video.split(' ')
                    for guild in guilds:
                        if split_title[0][1:] in guild.name or 'TP' in guild.name:  #
                            for channel in guild.channels:
                                if split_title[2][:-1].lower() in channel.name.lower() or 'test-bot' == channel.name.lower():
                                    embed = discord.Embed(
                                        title="Youtube video upload notification",
                                        description="{}".format(video),
                                        colour=discord.Colour.red()
                                    )
                                    thumb_url = self.videos.get(video)[1]
                                    foot = self.videos.get(video)[0]
                                    vid_id = self.videos.get(video)[2]
                                    foot = datetime.strptime(foot, "%Y-%m-%dT%H:%M:%SZ")
                                    embed.set_thumbnail(url=thumb_url['url'])
                                    embed.add_field(name='URL', value="https://youtube.com/watch?v={}".format(vid_id))
                                    embed.set_footer(text="Video uploaded : {}".format(foot))
                                    await channel.send(embed=embed)
            if count != 0:
                await self.update_db()


def setup(bot):
    bot.add_cog(Youtube(bot))
