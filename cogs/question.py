import string
import time

import discord.ext.commands.context
from discord.ext import commands

# TODO how to keep threads a live??? checking and pass message by bot near expiration???
# TODO probably remove messages in question and answers channel on_message not from bot, ideal disable write into this channel
# TODO add way how close reaction thread and store correct result/results


class Question(commands.Cog):
    def __init__(self, bot):
        self.activeChannelName = "active-questions"
        self.activeChannelTopic = "This channel contains not resolved questions"

        self.archivedChannelName = "archived-questions"
        self.archivedChannelTopic = "This channel is archive of resolved questions"

        self.channelsCategoryName = "Question-bot channels"
        self.bot = bot

    @commands.group(aliases=["q"], invoke_without_command=True, description="Príkaz na položenie otázky")
    @commands.guild_only()
    async def question(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), entity="question")

    @question.command(aliases=["c"], name="create", description="creates new question, wrap question into \" for question with spaces")
    @commands.guild_only()
    async def question_create(self, context: discord.ext.commands.context.Context, question):
        channel = await self.__getActiveQuestionsChannel(context.guild)
        question_embed = discord.Embed(
            color=self.bot.colors["BLUE"],
            description=f"{context.author.mention} is asking:\n\n" +
                        "***" + (question if question[-1] == "?" else question + "?").capitalize() + "***\n\n"
                        "__You can response into thread of this message__",
            title="Hi everyone, we need your help with the following question"
        )

        question_message = await channel.send(embed=question_embed)

        await channel.create_thread("Question: " + (question[0:15].strip() + "...") if len(question) > 15 else question, 24*60, question_message)
        await self.bot.question.upsert({"_id": question_message.id, "last_activity": round(time.time())})
        await context.message.delete()

    async def __createCategory(self, guild: discord.guild):
        return await guild.create_category(self.channelsCategoryName, position=0)

    async def __createChannel(self, guild, category, name: string, topic: string):
        channel = await guild.create_text_channel(name)
        await channel.edit(category=category, topic=topic)

        return channel

    async def __createChannels(self, guild: discord.guild):
        category = await self.__getChannelCategory(guild)
        active_channel = await self.__createChannel(
            guild, category, self.activeChannelName, self.activeChannelTopic
        )
        archived_channel = await self.__createChannel(
            guild, category, self.archivedChannelName, self.archivedChannelTopic
        )

        await self.bot.guild_question_channel.upsert({
            "active_channel_id": active_channel.id, "archived_channel_id": archived_channel.id, "_id": guild.id
        })

        return [category, active_channel, archived_channel]

    async def __getChannelCategory(self, guild: discord.guild):
        for category in guild.categories:
            if category.name == self.channelsCategoryName:
                return category

        return await self.__createCategory(guild)

    async def __getActiveQuestionsChannel(self, guild: discord.guild):
        channel_record = await self.bot.guild_question_channel.find_by_id(guild.id)
        active_channel = None

        if channel_record is not None:
            active_channel = guild.get_channel(channel_record["active_channel_id"])

        if active_channel is None:
            [_, active_channel, _] = await self.__createChannels(guild)

        return active_channel


def setup(bot):
    bot.add_cog(Question(bot))
