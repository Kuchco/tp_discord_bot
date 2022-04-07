import asyncio
import string
import time

import discord.ext.commands.context
from discord import TextChannel
from discord.ext import commands

import utils.util
from core.base_command import BaseCommand


class Question(BaseCommand):
    def __init__(self, bot):
        super().__init__(bot)
        self.activeChannelName = "active-questions"
        self.activeChannelTopic = "This channel contains not resolved questions"

        self.archivedChannelName = "archived-questions"
        self.archivedChannelTopic = "This channel is archive of resolved questions"

        self.errorAnswerWithReactionNotFound = "In thread doesn't exist message emoji-marked by you as answer"
        self.errorUsableOnlyInThread = "Command is usable only inside question thread"

        self.channelsCategoryName = "Question-bot channels"
        self.channelsRoleName = "questions-manager"

        self.question_prefix = "is asking:\n\n***"
        self.question_postfix = "***\n\n__You can response into thread of this message__"

        self.inactiveThreadDurationInS = 24 * 60 * 60
        self.inactiveThreadCheckEveryInS = 60 * 60
        self.inactiveThreadReminderBeforeExpirationInS = self.inactiveThreadCheckEveryInS * 3

    @commands.Cog.listener()
    async def on_ready(self):
        await super().on_ready()
        await self.__startThreadActivityReSpawner()

    @commands.guild_only()
    @commands.group(aliases=["q"], invoke_without_command=True, description="Group of commands determined for the Q&A system")
    async def question(self, context: discord.ext.commands.context.Context) -> None:
        await context.invoke(self.bot.get_command("help"), entity="question")

    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @question.command(aliases=["a"], name="answer", description="Answers (resolves) question, usable only inside active question thread. Wrap answer into \" for question with spaces")
    async def question_answer(self, context: discord.ext.commands.context.Context, answer) -> None:
        question = await self.bot.question.find_by_id(context.channel.id)
        if question is not None:
            await (await self.__getArchivedQuestionsChannel(context.guild)).send(
                embed=await self.__getQuestionAnswerEmbed(context, question["_id"], [answer])
            )
            await self.__removeQuestion(context, question["_id"])
        else:
            await self.__sendErrorMessage(context, self.errorUsableOnlyInThread)

    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @question.command(aliases=["aem"], name="answer-emoji-marked", description="Answers (resolves) question with specific emoji marked messages. Usable only inside active question thread.")
    async def question_answer_emoji_marked(self, context: discord.ext.commands.context.Context, emoji) -> None:
        question = await self.bot.question.find_by_id(context.channel.id)
        if question is not None:
            answers = []
            async for message in context.history(oldest_first=True):
                if self.bot.user.id == message.author.id:
                    continue

                if await self.__isMessageMarkedByUserWithEmoji(message, context.author.id, emoji):
                    answers.append(message.content)

            if len(answers) > 0:
                await (await self.__getArchivedQuestionsChannel(context.guild)).send(
                    embed=await self.__getQuestionAnswerEmbed(context, question["_id"], answers)
                )
                await self.__removeQuestion(context, question["_id"])
            else:
                await self.__sendErrorMessage(context, self.errorAnswerWithReactionNotFound)
        else:
            await self.__sendErrorMessage(context, self.errorUsableOnlyInThread)

    @commands.guild_only()
    @question.command(aliases=["c"], name="create", description="Creates new question, wrap question into \" for question with spaces")
    async def question_create(self, context: discord.ext.commands.context.Context, question) -> None:
        channel = await self.__getActiveQuestionsChannel(context.guild)
        question_embed = discord.Embed(
            color=self.bot.colors["BLUE"],
            description=f"{context.author.mention} " + self.question_prefix +
                        (question if question[-1] == "?" else question + "?").capitalize() +
                        self.question_postfix,
            title="Hi everyone, we need your help with the following question"
        )

        question_message = await channel.send(embed=question_embed)

        await channel.create_thread(
            name="Question #" + ((question[0:15].strip() + "...") if len(question) > 15 else question),
            message=question_message, auto_archive_duration=round(self.inactiveThreadDurationInS / 60),
        )

        await self.bot.question.upsert({
            "_id": question_message.id, "guild_id": context.guild.id, "last_activity": round(time.time()), "remind_msg_id": None
        })

        await context.message.delete()

    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @question.command(aliases=["r", "delete", "d"], name="remove", description="Removes question, usable only inside active question thread.")
    async def question_remove(self, context: discord.ext.commands.context.Context) -> None:
        question = await self.bot.question.find_by_id(context.channel.id)
        if question is not None:
            await self.__removeQuestion(context, question["_id"])
        else:
            await self.__sendErrorMessage(context, self.errorUsableOnlyInThread)

    async def __createCategory(self, guild: discord.guild):
        return await guild.create_category(self.channelsCategoryName, position=0)

    async def __createChannel(self, guild: discord.guild, category: discord.CategoryChannel, name: string, role: discord.Role, topic: string) -> TextChannel:
        channel = await guild.create_text_channel(name, category=category, topic=topic)

        await channel.set_permissions(role, administrator=True)
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

    async def __getActiveQuestionsChannel(self, guild: discord.guild) -> TextChannel:
        return await self.__getQuestionChannel(guild, "active_channel_id")

    async def __getArchivedQuestionsChannel(self, guild: discord.guild) -> TextChannel:
        return await self.__getQuestionChannel(guild, "archived_channel_id")

    async def __getChannelCategory(self, guild: discord.guild) -> discord.CategoryChannel:
        for category in guild.categories:
            if category.name == self.channelsCategoryName:
                return category

        return await self.__createCategory(guild)

    async def __getQuestionAnswerEmbed(self, context: discord.ext.commands.context.Context, question_id: int, answers: []) -> discord.Embed:
        # TODO change - for layout "-"
        # TODO underline first line with author, every answer should be on own line, include one line ones
        merged_answer = ""
        for answer in answers:
            if len(answers) > 1:
                merged_answer += "\n - "
            merged_answer += answer.capitalize()

        raw_question_message = (await (await self.__getActiveQuestionsChannel(context.guild)).fetch_message(question_id)).embeds[0].description
        message_start = raw_question_message.find(self.question_prefix) + len(self.question_prefix)
        message_end = raw_question_message.find(self.question_postfix)

        return discord.Embed(
            color=self.bot.colors["GREEN"],
            description=f"{context.author.mention} solved question with answer: ***" + merged_answer + "***\n\n",
            title=raw_question_message[message_start:message_end],
        )

    async def __getQuestionChannel(self, guild: discord.guild, channel_id: string) -> discord.TextChannel:
        channel_record = await self.bot.guild_question_channel.find_by_id(guild.id)
        channel = None

        if channel_record is not None:
            channel = guild.get_channel(channel_record[channel_id])

        if channel is None:
            [_, channels] = await self.__setup(guild)
            channel = channels[channel_id]

        return channel

    async def __isMessageMarkedByUserWithEmoji(self, message: discord.Message, user_id: int, emoji: string) -> bool:
        answer_reaction = discord.utils.get(message.reactions, emoji=emoji)

        if answer_reaction is not None:
            async for user in answer_reaction.users():
                if user.id == user_id:
                    return True

        return False

    async def __removeQuestion(self, context: discord.ext.commands.context.Context, question_id: int) -> None:
        await context.channel.parent.get_partial_message(question_id).delete()
        await context.channel.delete()
        await self.bot.question.delete(context.channel.id)

    async def respawnQuestionThreadsActivity(self) -> None:
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
                    if thread is None:
                        continue

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

    async def __sendErrorMessage(self, context: discord.ext.commands.context.Context, text: string) -> None:
        await context.channel.send(embed=discord.Embed(color=self.bot.colors["RED"], title=text))

    async def __setup(self, guild: discord.guild):
        category = await self.__getChannelCategory(guild)
        role = await self.__setupRole(guild)

        active_channel = await self.__createChannel(guild, category, self.activeChannelName, role, self.activeChannelTopic)
        archived_channel = await self.__createChannel(guild, category, self.archivedChannelName, role, self.archivedChannelTopic)

        await self.bot.guild_question_channel.upsert({
            "active_channel_id": active_channel.id, "archived_channel_id": archived_channel.id, "_id": guild.id
        })

        return [category, {"active_channel_id": active_channel, "archived_channel_id": archived_channel}]

    async def __setupRole(self, guild: discord.guild) -> discord.Role:
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

    async def __startThreadActivityReSpawner(self) -> None:
        while True:
            await self.respawnQuestionThreadsActivity()
            await asyncio.sleep(self.inactiveThreadCheckEveryInS)


def setup(bot) -> None:
    bot.add_cog(Question(bot))
