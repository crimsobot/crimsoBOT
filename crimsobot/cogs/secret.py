import discord
from discord.ext import commands

from crimsobot.bot import CrimsoBOT
from crimsobot.utils.games import win
from crimsobot.utils.tools import crimbed


class Secret(commands.Cog):
    def __init__(self, bot: CrimsoBOT):
        self.bot = bot

        self.done = False
        self.mentions = 0

        self.message_id = None
        self.reacted = []

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.done:
            return

        if not isinstance(message.channel, discord.TextChannel):
            return

        if not message.guild:
            return

        if not message.guild.id == 280298381807714304:
            return

        unique_ids = set([u.id for u in message.mentions])
        for uid in unique_ids:
            if uid in (132924988100444160, 344311324295036928, 189458972657319936):
                self.mentions += 1

        if self.mentions >= 11_000:
            self.done = True
            embed = crimbed(
                title='BIRTHDAY MONEY',
                descr='\n'.join([
                    "Congratulations, Ooers, we've reached 11,000 birthday pings!",
                    "You've unlocked free crimsoCOIN for the entire server!",
                    "Click the crimsoCOIN reaction below to claim your 200 coins!",
                ]),
                thumb_name='jester',
            )
            channel = self.bot.get_channel(381181788111896587)
            final_message = await channel.send(embed=embed)
            self.message_id = final_message.id
            await final_message.add_reaction('<:crimsoCOIN:588558997238579202>')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, event):
        if not event.message_id == self.message_id:
            return

        if not event.emoji.id == 588558997238579202:
            return

        if event.user_id in self.reacted:
            return

        if event.member and not self.bot.is_banned(event.member):
            self.reacted.append(event.member.id)
            await win(event.member, 200)


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Secret(bot))
