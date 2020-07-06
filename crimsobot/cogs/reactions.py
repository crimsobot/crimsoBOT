import logging

from discord.ext import commands
from discord.ext.commands import has_guild_permissions
from tortoise.exceptions import DoesNotExist

from config import ADMIN_USER_IDS
from crimsobot.bot import CrimsoBOT
from crimsobot.models.fun_facts import FunFacts, NoFactsExist
from crimsobot.utils import tools as c

log = logging.getLogger(__name__)


class CleanMentions(commands.Converter):
    async def convert(self, ctx: commands.Context, string: str) -> str:
        """Clean up those silly mention inconsistencies across platforms."""
        for mention in ctx.message.mentions:
            string = string.replace(f'<@!{mention.id}>', f'<@{mention.id}>', 1)

        return string


class Reactions(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

    @commands.group(aliases=['facts'])
    async def fact(self, ctx: commands.Context) -> None:
        """Testing out facts."""
        return

    @fact.command(name='about')
    async def fact_about(self, ctx: commands.Context, *, subject: CleanMentions) -> None:
        """Write up some HELP"""
        try:
            fact_object = await FunFacts.get_by_subject(subject.lower().strip(), ctx.guild.id)
        except NoFactsExist:
            embed = c.crimbed(
                title='OMAN',
                descr=f'There are no facts about {subject}!',
                footer='You can add one by using ">fact about [fact subject]; [some fun fact]"',
                color_name='yellow',
                thumb_name='weary',
            )
            await ctx.send(embed=embed, delete_after=18)
            return

        return_string = ''.join([
            f'`Fact ID: {fact_object.uuid}` · ',
            f"**Here's a fact about {fact_object.subject.upper()}**:\n\n",
            f'{fact_object.funfact}\n\n',
        ])

        await ctx.send(return_string)

    @fact.command(name='add')
    async def fact_add(self, ctx: commands.Context, *, something: CleanMentions) -> None:
        """Add a fact"""

        # if there are any errors in user input, use this embed
        error_embed = c.crimbed(
            title='BAD AT COMPUTER',
            descr="You didn't do that correctly! Try this:\n`>fact add your subject; your fact`",
            footer='You can always check ">help fact" for more info!',
            color_name='yellow',
            thumb_name='weary',
        )

        # see if there are uploaded files or media
        try:
            link_list = []
            for link in ctx.message.attachments:
                link_list.append(link.url)
            links = '\n'.join(link_list)
        except IndexError:
            links = ''

        user_input = something.split(';', 1)

        fact_subject = user_input.pop(0).strip().lower()
        try:
            fact = f'{user_input[0].strip()} {links}'
        except IndexError:
            await ctx.send(embed=error_embed, delete_after=18)
            return

        if len(fact_subject) < 1 or len(fact) < 1:
            await ctx.send(embed=error_embed, delete_after=18)
            return

        new_fact = await FunFacts.create_fact(ctx.author, ctx.guild.id, fact_subject, fact)

        if new_fact:
            embed = c.crimbed(
                title=None,
                descr='Fact added!',
                footer=f'Fact ID: {new_fact.uuid}'
            )
            await ctx.send(embed=embed)

    @fact.command(name='inspect')
    async def fact_inspect(self, ctx: commands.Context, fact_id: int) -> None:
        # check if owner for server-specific override
        owner = ctx.author.id in ADMIN_USER_IDS

        try:
            fact_object = await FunFacts.get_by_id(fact_id, ctx.guild.id, owner)
        except DoesNotExist:
            embed = c.crimbed(title=None, descr=f'Fact {fact_id} does not exist (at least not in this server)!')
            await ctx.send(embed=embed, delete_after=18)
            return

        fact_adder = self.bot.get_user(fact_object.created_by.discord_user_id)

        guild = self.bot.get_guild(fact_object.created_in)

        embed = c.crimbed(
            title=f'FACT INSPECT // ID: {fact_object.uuid}' + ' (admin view)' if owner else '',
            descr=None,
            footer='Users with Manage Messages permission can remove facts using ">fact remove [ID]"',
            thumb_name='think',
            color_name='yellow',
        )

        field_list = [
            ('Subject', fact_object.subject),
            ('Body', fact_object.funfact),
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

    @fact.command(name='remove', aliases=['delete'], brief='Remove a fact by ID.')
    @has_guild_permissions(manage_messages=True)
    async def remove_fact(self, ctx: commands.Context, fact_id: int) -> None:
        """Remove a fact by its ID. To use this command, you must have Manage Messages permission."""
        # check if owner for server-specific override
        owner = ctx.author.id in ADMIN_USER_IDS

        fact_removed = await FunFacts.delete_by_id(fact_id, ctx.guild.id, owner)

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
                  brief='Remove all facts of a given subject')
    @has_guild_permissions(manage_messages=True)
    async def remove_subject(self, ctx: commands.Context, *, subject: CleanMentions) -> None:
        """Remove all facts in a server with the same subject. Useful for removing spam."""
        facts_removed = await FunFacts.delete_by_subject(subject, ctx.guild.id)

        if facts_removed != 0:
            embed = c.crimbed(title=None, descr=f'All {facts_removed} **{subject}** facts removed from this server!')
        else:
            embed = c.crimbed(
                title=None,
                descr='This subject was not removed!',
                footer='· Did you input the correct subject?\n· Were these facts created in this server?',
            )

        await ctx.send(embed=embed, delete_after=18)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Reactions(bot))
