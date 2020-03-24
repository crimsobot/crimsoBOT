import os
import random

from discord.ext import commands

from config import ADMIN_USER_IDS, SCRAPER_USER_IDS
from crimsobot.bot import CrimsoBOT
from crimsobot.utils import markov as m, tools as c


class Chat(commands.Cog):
    def __init__(self, bot: CrimsoBOT) -> None:
        self.bot = bot

    @commands.command()
    async def scatterbrain(self, ctx: commands.Context) -> None:
        """Short-term memory mania."""

        messages = []

        # grab message contents (which are strings):
        async for message in ctx.channel.history(limit=500):
            if message.author.id != self.bot.user.id:
                messages.append(message.content)

        output = m.scatter(messages)
        await ctx.send(output)

    @commands.command()
    async def poem(self, ctx: commands.Context) -> None:
        """Spits out a poem."""

        fake_author = [
            ('Crimso Allen Poe', 1827, 1848),
            ('Maya Crimsolou', 1969, 2013),
            ('Crimbert Frost', 1894, 1959),
            ('Crumi', 1225, 1260),
            ('William Crimsworth', 1793, 1843),
            ('t.s. crimsiot', 1910, 1958),
            ('Crimily Dickinson', 1858, 1886),
            ('William Crimso Williams', 1910, 1962),
            ('Crymsia Plath', 1960, 1963),
            ('Crimtrude Stein', 1909, 1933),
            ('Allen Crimsberg', 1950, 1997),
        ]

        choice = random.choice(fake_author)

        generated_poem = await m.async_wrap(self.bot, m.poem, int(random.gauss(5, 1)))
        embed = c.crimbed(
            title='**A poem.**',
            descr=generated_poem.lower(),
            footer='{}, {}'.format(choice[0], random.randint(choice[1], choice[2])),
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def wisdom(self, ctx: commands.Context) -> None:
        """Crimsonic wisdom."""

        embed = c.crimbed(
            title='**CRIMSONIC WISDOM**',
            descr=m.wisdom(),
            thumb_name='think',
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=['monty'])
    async def montyward(self, ctx: commands.Context) -> None:
        """Monty mindfuck!"""

        footer_text = [
            'Those black spots on your bananas? Those are tarantula eggs.',
            "You don't know Monty but he knows you.",
            'Look behind you. Now to your left. Now your right! Nevermind, Monty is already gone.',
            "You wrote this story before you fell into the coma. Don't bother waking up, the world is ending.",
            'You know that urge you have to scratch the itch behind your eyelids? Those are the worms.',
            "Scream if you must, it won't do you any good.",
            "Word to the wise: don't look at the moon."
        ]

        embed = c.crimbed(
            title='An excerpt from **THE FIRST NECROMANCER (sort of)**, by Monty Ward',
            descr=await m.async_wrap(self.bot, m.rovin),
            thumb_name='monty',
            footer='{} Sleep tight.'.format(random.choice(footer_text)),
        )
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def scrape(self, ctx: commands.Context, place: str = 'here', join: str = 'space', n: int = 10000) -> None:
        """Scrape messages from channel. >scrape [here/dm/channel_id] [space/newline]."""

        if ctx.message.author.id not in ADMIN_USER_IDS | SCRAPER_USER_IDS:
            return

        file = c.clib_path_join('text', 'scrape.txt')
        if os.path.exists(file):
            os.remove(file)

        channel = ctx.message.channel
        await ctx.message.delete()

        # grab message contents (which are strings):
        async for msg in channel.history(limit=n):
            if not msg.pinned:
                m.scraper(msg.content)

        text = []
        for line in reversed(list(open(file, encoding='utf8', errors='ignore'))):
            text.append(line.rstrip())

        # haiku only
        for i in range(len(text)):
            if (i + 1) % 3 == 0:
                text[i] = text[i] + '\n\u200A'

        if join == 'space':
            joiner = ' '
        elif join == 'newline':
            joiner = '\n'
        else:
            raise commands.BadArgument('Join type is invalid.')

        msgs = c.crimsplit(joiner.join(text), '\u200A', 1950)
        try:
            if place == 'dm':
                dest = ctx.message.author
            elif place == 'here':
                dest = ctx.message.channel
            else:
                dest = self.bot.get_channel(place)
        except AttributeError:
            raise commands.BadArgument('Destination is invalid.')

        for msg in msgs:
            await dest.send(msg)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Chat(bot))
