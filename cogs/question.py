import asyncio
import string
import time

import discord.ext.commands.context
from discord.ext import commands

# TODO add way how close reaction thread and store correct result/results
import utils.util
from core.base_command import BaseCommand


class Question(BaseCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self.activeChannelName = "active-questions"
        self.activeChannelTopic = "This channel contains not resolved questions"

        self.archivedChannelName = "archived-questions"
        self.archivedChannelTopic = "This channel is archive of resolved questions"

        self.channelsCategoryName = "Question-bot channels"
        self.channelsRoleName = "questions-manager"

        self.inactiveThreadDurationInS = 24 * 60 * 60
        self.inactiveThreadCheckEveryInS = 60 * 60
        self.inactiveThreadReminderBeforeExpirationInS = self.inactiveThreadCheckEveryInS * 3

    @commands.Cog.listener()
    async def on_ready(self):
        await super().on_ready()
        await self.__start_thread_activity_checker()

    @commands.group(aliases=["q"], invoke_without_command=True, description="Príkaz na položenie otázky")
    @commands.guild_only()
    async def question(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), entity="question")

    @question.command(name="cancel", description="cancel question, use inside question thread")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def question_cancel(self, context: discord.ext.commands.context.Context):
        question = await self.bot.question.find_by_id(context.channel.id)
        if question is not None:
            await context.channel.parent.get_partial_message(question["_id"]).delete()
            await context.channel.delete()
            await self.bot.question.delete(context.channel.id)
        else:
            await context.channel.send(embed=discord.Embed(
                color=self.bot.colors["RED"],
                title="Usable only in question thread"
            ))

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

        await channel.create_thread(
            name="Question #" + ((question[0:15].strip() + "...") if len(question) > 15 else question),
            message=question_message, auto_archive_duration=self.inactiveThreadDurationInS / 60,
        )

        await self.bot.question.upsert({
            "_id": question_message.id, "guild_id": context.guild.id, "last_activity": round(time.time()), "remind_msg_id": None
        })

        await context.message.delete()

    async def __check_threads_activity(self):
        for question in await self.bot.question.get_all():
            if question["last_activity"] + self.inactiveThreadDurationInS - self.inactiveThreadReminderBeforeExpirationInS > round(time.time()):
                continue

            guild_question_channel_record = await self.bot.guild_question_channel.find_by_id(question["guild_id"])
            if guild_question_channel_record is None:
                utils.util.log_error("Question exception: Removing " + format(question["_id"]) + " - cannot find its channel")
                await self.bot.question.delete(question["_id"])
                continue

            channel = self.bot.get_channel(guild_question_channel_record["active_channel_id"])
            try:
                message = await channel.fetch_message(question["_id"])
                if message.flags.has_thread:
                    thread = message.channel.get_thread(message.id)
                    if question["remind_msg_id"] is not None:
                        try:
                            remind_message = await thread.fetch_message(question["remind_msg_id"])
                            await remind_message.delete()
                        except discord.errors.NotFound:
                            utils.util.log_error("Question error: Not found last remind message of question: " + format(question["_id"]))

                    question["last_activity"] = round(time.time())
                    question["remind_msg_id"] = (
                        await thread.send(embed=discord.Embed(
                            color=self.bot.colors["ORANGE"],
                            title="Inactive question, please answer or close it if already answered"
                        ))
                    ).id

                    await self.bot.question.upsert(question)
                else:
                    utils.util.log_error("Question error: missing thread!")
            except discord.errors.NotFound:
                utils.util.log_error("Question exception: Removing " + format(question["_id"]) + " - no longer exist!")
                await self.bot.question.delete(question["_id"])

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

    async def __start_thread_activity_checker(self):
        while True:
            await self.__check_threads_activity()
            await asyncio.sleep(self.inactiveThreadCheckEveryInS)


def setup(bot):
    bot.add_cog(Question(bot))
