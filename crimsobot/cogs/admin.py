import datetime
import logging
from typing import Optional

import discord
from discord.ext import commands

from config import ADMIN_USER_IDS
from crimsobot.bot import CrimsoBOT
from crimsobot.models.ban import Ban
from crimsobot.models.user import User
from crimsobot.utils import tools as c

log = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot: CrimsoBOT) -> None:
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def ban(self, ctx: commands.Context, discord_user: discord.User) -> None:
        """Ban user from using crimsoBOT."""

        if discord_user.id in ADMIN_USER_IDS:
            return

        target = await User.get_by_discord_user(discord_user)  # type: User
        issuer = await User.get_by_discord_user(ctx.author)  # type: User
        await Ban.create(
            target=target,
            issuer=issuer,
            reason='Banned by admin'
        )

        self.bot.banned_user_ids.append(discord_user.id)

        embed = c.crimbed(
            None,
            '**{u.name}#{u.discriminator}** has been banned from using crimsoBOT.'.format(
                u=discord_user
            ),
            None
        )

        msg = await ctx.send(embed=embed)
        await msg.add_reaction('👺')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def unban(self, ctx: commands.Context, discord_user: discord.User) -> None:
        """Unban user from using crimsoBOT."""

        target = await User.get_by_discord_user(discord_user)  # type: User
        remover = await User.get_by_discord_user(ctx.author)  # type: User

        ban = await Ban.filter(target=target, active=True).first()  # type: Ban
        if ban:
            ban.active = False
            ban.remover = remover
            ban.removed_at = datetime.datetime.utcnow()
            await ban.save()

        self.bot.banned_user_ids.remove(discord_user.id)

        embed = c.crimbed(
            None,
            '**{u.name}#{u.discriminator}** has been unbanned from using crimsoBOT.'.format(
                u=discord_user
            ),
            None
        )

        msg = await ctx.send(embed=embed)
        await msg.add_reaction('🛐')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def banlist(self, ctx: commands.Context) -> None:
        """List of banned users."""

        banned_users = []
        for user_id in self.bot.banned_user_ids:
            discord_user = await self.bot.fetch_user(user_id)
            banned_users.append('· {u.name}#{u.discriminator}'.format(u=discord_user))

        if not banned_users:
            banned_users.append('No users are banned... yet')

        msg_string = '\n'.join(banned_users)
        msg_list = c.crimsplit(msg_string, '\n', limit=1990)
        for msg in msg_list:
            await ctx.send('```{}```'.format(msg))

    @commands.command()
    async def info(self, ctx: commands.Context) -> None:
        """crimsoBOT info and invites."""

        # change permissions integer here if need be
        auth_url = 'https://discordapp.com/api/oauth2/authorize?client_id={}&permissions={}&scope=bot'.format(
            self.bot.user.id,
            473300048
        )
        embed = c.crimbed(
            title='crimsoBOT info!',
            descr='crimsoBOT was born of boredom and is maintined from love.\n',
            thumb='https://i.imgur.com/9UTNIGi.png'
        )
        embed.add_field(
            name="crimsoBOT's Discord server",
            value='https://discord.gg/Kj3WNHX',
            inline=False
        )
        embed.add_field(
            name='Invite crimsoBOT to your server',
            value=auth_url,
            inline=False
        )
        embed.add_field(
            name='Support crimsoBOT server time, get a sticker!',
            value='https://www.patreon.com/crimso',
            inline=False
        )
        embed.add_field(
            name='Buy stickers and more *a la carte*!',
            value='https://crimobot.weebly.com/',
            inline=False
        )
        embed.set_footer(text='Thanks for using crimsoBOT!')

        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def servers(self, ctx: commands.Context) -> None:
        """List crimsoBOT's servers."""

        guilds = self.bot.guilds
        await ctx.send(
            '**Connected on {} servers:**\n'.format(len(guilds)) +
            '\n'.join('`[{g.id}]` | {g.name}'.format(g=guild) for guild in guilds)
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def serverinfo(self, ctx: commands.Context, server_id: Optional[int] = None) -> None:
        """Member count, owner, channel names, roles, and emojis."""

        if server_id is None:
            guild = ctx.message.guild
        else:
            guild = self.bot.get_guild(server_id)

        embed = c.get_guild_info_embed(guild)

        # ...and send
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            log.info("Guild info still too long, can't send...")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def save_from(self, ctx: commands.Context, server_id: int) -> None:
        """Pull crimsoBOT from a server."""

        guild = self.bot.get_guild(server_id)
        if guild:
            await guild.leave()
            log.info('crimsoBOT REMOVED from %s [%s]', guild, guild.id)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx: commands.Context) -> None:
        """Reload all extensions. Intended for local development."""

        self.bot.reload_extensions()
        log.info('All extensions have been reloaded.')


def setup(bot: CrimsoBOT) -> None:
    bot.add_cog(Admin(bot))
