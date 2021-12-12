import discord.ext.commands.context
from discord.ext import commands


class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @commands.has_guild_permissions(administrator=True)
    # @commands.has_guild_permissions(manage_roles=True)

    @commands.group(aliases=["q"], invoke_without_command=True, description="Príkaz na položenie otázky")
    @commands.guild_only()
    async def question(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), entity="question")

    @question.command(aliases=["c"], name="create", description="creates new question, wrap question into \" for question with spaces")
    @commands.guild_only()
    async def question_create(self, context: discord.ext.commands.context.Context, question):
        channel = await self.__getQuestionChannel(context.guild)
        question = discord.Embed(
            color=self.bot.colors["BLUE"],
            description=f"{context.author.mention} is asking:\n\n" +
                        "***" + (question if question[-1] == "?" else question + "?").capitalize() + "***\n\n"
                        "__You can response into thread of this message__",
            title="Hi everyone, we need your help with the following question"
        )

        question_message = await channel.send(embed=question)
        # TODO create thread if possible
        await context.message.delete()

    async def __getQuestionChannel(self, guild: discord.guild):
        channel_record = await self.bot.guild_question_channel.find_by_id(guild.id)
        guild_channel = None

        if channel_record is not None:
            guild_channel = guild.get_channel(channel_record["channel_id"])

        if guild_channel is None:
            guild_channel = await self.__createQAndAChannel(guild)
            await self.bot.guild_question_channel.upsert({"channel_id": guild_channel.id, "_id": guild.id})

        return guild_channel

    async def __createQAndAChannel(self, guild: discord.guild):
        channel = await guild.create_text_channel("question-and-answer")
        # TODO probably set permissions, description, etc

        return channel


def setup(bot):
    bot.add_cog(Question(bot))
