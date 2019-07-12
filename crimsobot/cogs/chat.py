import os
import random

from discord.ext import commands

from config import ADMIN_USER_IDS, SCRAPER_USER_IDS
from crimsobot.utils import markov as m, tools as c


class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def scatterbrain(self, ctx):
        """Short-term memory mania."""

        channel = ctx.message.channel
        messages = []

        # grab message contents (which are strings):
        async for message in channel.history(limit=500):
            if message.author.id != self.bot.user.id:
                messages.append(message.content)

        output = m.scatter(messages)
        await ctx.send(output)

    @commands.command(hidden=True)
    async def scrape(self, ctx, place='here', join='space', n=10000):
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

        text = joiner.join(text)

        msgs = c.crimsplit(text, '\u200A', 1950)
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

    @commands.command()
    async def poem(self, ctx):
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

        descr = m.poem(int(random.gauss(5, 1)))
        embed = c.crimbed('**A poem.**', descr.lower(), None)
        choice = random.randint(0, len(fake_author) - 1)
        embed.set_footer(text='{}, {}'.format(
            fake_author[choice][0],
            random.randint(fake_author[choice][1], fake_author[choice][2])
        ))

        await ctx.send(embed=embed)

    @commands.command()
    async def wisdom(self, ctx):
        """Crimsonic wisdom."""

        embed = c.crimbed('**CRIMSONIC WISDOM**', m.wisdom(), None)
        await ctx.send(embed=embed)

    @commands.command(aliases=['monty'])
    async def montyward(self, ctx):
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

        title = 'An excerpt from **THE FIRST NECROMANCER (sort of)**, by Monty Ward'
        descr = m.rovin()
        embed = c.crimbed(title, descr, 'https://i.imgur.com/wOFf7PF.jpg')
        embed.set_footer(text=random.choice(footer_text) + ' Sleep tight.')

        await ctx.send(embed=embed)

    # @commands.command(hidden=True)
    # async def final(self, ctx):
    #     await ctx.send('`Final warning...`')
    #
    #     channel = ctx.message.channel
    #     now = datetime.utcnow()
    #     then = now.replace(hour=2, minute=25)
    #
    #     # grab message contents (which are strings):
    #     async for message in channel.history(limit=10000):
    #         if message.author.id in ADMIN_USER_IDS and message.created_at > then:
    #             m.learner(message.content)
    #
    #     await ctx.send('`Task complete.`')


def setup(bot):
    bot.add_cog(Chat(bot))
