import string
import time

import discord.ext.commands.context
from discord.ext import commands

# TODO how to keep threads a live??? checking and pass message by bot near expiration???
# TODO add way how close reaction thread and store correct result/results


class Question(commands.Cog):
    def __init__(self, bot):
        self.activeChannelName = "active-questions"
        self.activeChannelTopic = "This channel contains not resolved questions"

        self.archivedChannelName = "archived-questions"
        self.archivedChannelTopic = "This channel is archive of resolved questions"

        self.channelsCategoryName = "Question-bot channels"
        self.channelsRoleName = "questions-manager"
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

    async def __createChannel(self, guild, category, name: string, question_manager_role, topic: string):
        channel = await guild.create_text_channel(name, category=category, topic=topic)

        await channel.set_permissions(question_manager_role, administrator=True)
        await channel.set_permissions(
            guild.default_role,
            administrator=False,
            manage_channels=False,
            manage_permissions=False,
            manage_messages=False,
            read_messages=True,
            send_messages=False
        )

        return channel

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
            [_, active_channel, _] = await self.__setup(guild)

        return active_channel

    async def __setup(self, guild: discord.guild):
        category = await self.__getChannelCategory(guild)
        question_manager_role = await self.__setupRole(guild)

        active_channel = await self.__createChannel(
            guild, category, self.activeChannelName, question_manager_role, self.activeChannelTopic
        )
        archived_channel = await self.__createChannel(
            guild, category, self.archivedChannelName, question_manager_role, self.archivedChannelTopic
        )

        await self.bot.guild_question_channel.upsert({
            "active_channel_id": active_channel.id, "archived_channel_id": archived_channel.id, "_id": guild.id
        })

        return [category, active_channel, archived_channel]

    async def __setupRole(self, guild: discord.guild):
        question_manager_role = None
        for role in guild.roles:
            if role.name == self.channelsRoleName:
                question_manager_role = role
                break

        if question_manager_role is None:
            question_manager_role = await guild.create_role(
                colour=self.bot.colors["WHITE"],
                hoist=True,
                name=self.channelsRoleName,
                permissions=discord.Permissions.all()
            )

        await (await guild.fetch_member(self.bot.user.id)).add_roles(question_manager_role)

        return question_manager_role


def setup(bot):
    bot.add_cog(Question(bot))
