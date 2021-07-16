import logging

from discord.ext import commands
from discord.ext.commands import has_guild_permissions
from tortoise.exceptions import DoesNotExist

from config import ADMIN_USER_IDS
from crimsobot.bot import CrimsoBOT
from crimsobot.models.fun_fact import FunFact, NoFactsExist
from crimsobot.utils import tools as c
from crimsobot.utils.converters import CleanMentions
from crimsobot.utils.fact_leaderboard import FactLeaderboard

log = logging.getLogger(__name__)


class Reactions(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    @commands.group(aliases=['facts'], invoke_without_command=True, brief='Add and look up facts!')
    async def fact(self, ctx: commands.Context, *, subject: CleanMentions = None) -> None:
        """Facts is a feature that allows users to add and look up facts in their server.
        Use >help fact [command] for more info about the subcommands below.
        """

        if subject:
            await self.fact_about.can_run(ctx)
            await self.fact_about(ctx, subject=subject)
            return

        # fallback to random fact if no proper arguments are provided
        await self.fact_random(ctx)

    @fact.command(name='about', brief='Get a fact about a subject!')
    async def fact_about(self, ctx: commands.Context, *, subject: CleanMentions) -> None:
        """Looks up a random fact about the given subject.
        If you want to look up a specific fact, use >fact inspect.
        You will need to know that fact's ID """

        try:
            fact_object = await FunFact.get_by_subject(subject.lower().strip(), ctx.guild.id)
        except NoFactsExist:
            embed = c.crimbed(
                title='OMAN',
                descr=f'There are no facts about **{subject}**!',
                footer='You can add one by using ">fact add [fact subject]; [some fun fact]"',
                color_name='yellow',
                thumb_name='weary',
            )
            await ctx.send(embed=embed, delete_after=18)
            return

        return_string = ''.join([
            f'`Fact ID: {fact_object.uid}` · ',
            f"Here's a fact about **{fact_object.subject.upper()}**:\n\n",
            f'{fact_object.body}',
        ])

        await ctx.send(return_string)

    @fact.command(name='add', brief='Add a fact!')
    @commands.cooldown(1, 9, commands.BucketType.user)
    async def fact_add(self, ctx: commands.Context, *, something: CleanMentions) -> None:
        """Add a fact to your server's database of facts. Anyone can add a fact.
        Fact subjects can be multiple words separated by spaces. Facts can include uploaded files and media.

        Example usage: >fact add your subject; your fact
        """

        # if there are any errors in user input, use this embed
        error_embed = c.crimbed(
            title='BAD AT COMPUTER',
            descr="You didn't do that correctly! Try this:\n`>fact add your subject; your fact`",
            footer='You can always check ">help fact" for more info!',
            color_name='yellow',
            thumb_name='weary',
        )

        # see if there are uploaded files or media
        link_list = [link.url for link in ctx.message.attachments]
        links = '\n'.join(link_list)

        user_input = something.split(';', 1)

        fact_subject = user_input[0].strip().lower()

        # if the user entered a subject body, use it
        # and add any attachments
        try:
            fact = f'{user_input[1].strip()} {links}'
        except IndexError:
            # if there is no body but there are still attachments,
            # use just the attachments as the body
            if links:
                fact = links
            else:
                await ctx.send(embed=error_embed, delete_after=18)
                return

        if len(fact_subject) < 1 or len(fact) < 2:
            await ctx.send(embed=error_embed, delete_after=18)
            return

        fact, is_new = await FunFact.create_fact(ctx.author, ctx.guild.id, fact_subject, fact)

        embed = c.crimbed(
            title=None,
            descr='Fact added!' if is_new else 'That fact already exists!',
            footer=f'Fact ID: {fact.uid}'
        )

        await ctx.send(embed=embed)

    @fact.command(name='inspect', brief='Get more info about a specific fact!')
    async def fact_inspect(self, ctx: commands.Context, fact_id: int) -> None:
        """Use this command to look up information about any fact on your server.
        You will need a fact's ID, which is at the beginning of each fact when it shows up in the server.
        """

        # check if owner for server-specific override
        owner = ctx.author.id in ADMIN_USER_IDS

        try:
            fact_object = await FunFact.get_by_id(fact_id, ctx.guild.id, owner)
        except DoesNotExist:
            embed = c.crimbed(title=None, descr=f'Fact {fact_id} does not exist (at least not in this server)!')
            await ctx.send(embed=embed, delete_after=18)
            return

        fact_adder = self.bot.get_user(fact_object.created_by.discord_user_id)

        guild = self.bot.get_guild(fact_object.guild_id)

        embed = c.crimbed(
            title=f'FACT INSPECT // ID: {fact_object.uid}' + ' (admin view)' if owner else '',
            descr=None,
            footer='Users with the Manage Messages permission can remove facts using ">fact remove [ID]"',
            thumb_name='nerd',
            color_name='yellow',
        )

        field_list = [
            ('Subject', fact_object.subject),
            ('Body', fact_object.body[:500] + '...' if len(fact_object.body) > 500 else fact_object.body),
            ('Added by', f'{fact_adder} ({fact_adder.id})'),
            ('Server', f'{guild.name} ({guild.id})'),
            (
                'Added on',
                '{d.year}-{d.month:02d}-{d.day:02d} {d.hour:02d}:{d.minute:02d}:{d.second:02d}'.format(
                    d=fact_object.created_at)
            ),
        ]

        for field in field_list:
            embed.add_field(name=field[0], value=field[1], inline=False)

        await ctx.send(embed=embed)

    @fact.command(name='random', brief='Random fact from this server!')
    async def fact_random(self, ctx: commands.Context) -> None:
        """Looks up a random fact in the server.
        If you want to look up a fact about a specific subject, use >fact about [subject].
        """
        try:
            fact_object = await FunFact.get_random(ctx.guild.id)
        except NoFactsExist:
            embed = c.crimbed(
                title='OMAN',
                descr='There are no facts in this server!',
                footer='You can add one by using ">fact add [fact subject]; [some fun fact]"',
                color_name='orange',
                thumb_name='weary',
            )
            await ctx.send(embed=embed, delete_after=18)
            return

        return_string = ''.join([
            f'`Fact ID: {fact_object.uid}` · ',
            f"Here's a fact about **{fact_object.subject.upper()}**:\n\n",
            f'{fact_object.body}',
        ])

        await ctx.send(return_string)

    @fact.command(name='remove', aliases=['delete'], brief='Remove a fact by ID.')
    @has_guild_permissions(manage_messages=True)
    async def remove_fact(self, ctx: commands.Context, fact_id: int) -> None:
        """Remove a fact by its ID.
        To use this command, you must have the Manage Messages permission in your server."""

        # check if owner for server-specific override
        owner = ctx.author.id in ADMIN_USER_IDS

        fact_removed = await FunFact.delete_by_id(fact_id, ctx.guild.id, owner)

        if fact_removed != 0:
            embed = c.crimbed(title=None, descr=f'Fact {fact_id} removed!')
        else:
            embed = c.crimbed(
                title=None,
                descr='This fact was not removed!',
                footer='· Did you input the correct fact ID?\n· Was this fact created in this server?',
            )

        await ctx.send(embed=embed, delete_after=18)

    @fact.command(name='wipe', aliases=['remove_subject', 'delete_subject'],
                  brief='Remove all facts of a given subject.')
    @has_guild_permissions(manage_messages=True)
    async def remove_subject(self, ctx: commands.Context, *, subject: CleanMentions) -> None:
        """Remove all facts in a server with the same subject. Useful for removing spam.
        To use this command, you must have the Manage Messages permission in your server."""

        facts_removed = await FunFact.delete_by_subject(subject, ctx.guild.id)

        if facts_removed:
            embed = c.crimbed(title=None, descr=f'All {facts_removed} **{subject}** facts removed from this server!')
        else:
            embed = c.crimbed(
                title=None,
                descr='This subject was not removed!',
                footer='· Did you input the correct subject?\n· Were these facts created in this server?',
            )

        await ctx.send(embed=embed, delete_after=18)

    @fact.command(name='lb', aliases=['leaderboard'], brief='Facts leaderboard!')
    async def fact_leaderboard(self, ctx: commands.Context, page: int = 1) -> None:
        """Leaderboard for most facts by subject (server-specific)."""

        lb = FactLeaderboard(page)
        await lb.get_subject_leaders(ctx.guild.id)
        embed = await lb.get_embed(ctx)

        await ctx.send(embed=embed)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Reactions(bot))
