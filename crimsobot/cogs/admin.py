import logging

import discord
from discord.ext import commands

import crimsobot.utils.tools as c
from config import ADMIN_USER_IDS
from crimsobot.utils import checks
from crimsobot.utils.tools import CrimsoBOTUser

log = logging.getLogger(__name__)


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @checks.is_admin()
    async def ban(self, ctx, discord_user: discord.User):
        """Ban user from using crimsoBOT."""

        if discord_user.id in ADMIN_USER_IDS:
            return

        cb_user = CrimsoBOTUser.get(discord_user.id)
        cb_user.banned = True
        cb_user.save()

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
    @checks.is_admin()
    async def unban(self, ctx, discord_user: discord.User):
        """Unban user from using crimsoBOT."""

        cb_user = CrimsoBOTUser.get(discord_user.id)
        cb_user.banned = False
        cb_user.save()

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
    async def banlist(self, ctx):
        """List of banned users."""

        cb_user_object_list = c.who_is_banned()
        banned_users = []
        for user in cb_user_object_list:
            discord_user_object = await self.bot.fetch_user(user.ID)
            banned_users.append('· {u.name}#{u.discriminator}'.format(u=discord_user_object))

        if not banned_users:
            banned_users.append('No users are banned... yet')

        msg_string = '\n'.join(banned_users)
        msg_list = c.crimsplit(msg_string, '\n', limit=1990)
        for msg in msg_list:
            await ctx.send('```{}```'.format(msg))

    @commands.command(pass_context=True)
    async def info(self, ctx):
        """crimsoBOT info and invites."""

        title = 'crimsoBOT info'
        descr = 'crimsoBOT is a poorly-coded, homebrew bot.\n'
        thumb = 'https://i.imgur.com/9UTNIGi.png'
        auth_url = 'https://discordapp.com/api/oauth2/authorize?client_id={}&permissions={}&scope=bot'.format(
            self.bot.user.id,
            473300048
        )
        embed = c.crimbed(title, descr, thumb)
        embed.add_field(name="crimsoBOT's Discord server", value='https://discord.gg/Kj3WNHX', inline=False)
        embed.add_field(name='Invite crimsoBOT to your server', value=auth_url, inline=False)
        embed.add_field(
            name='Support crimsoBOT and get stickers!',
            value='https://www.patreon.com/crimso',
            inline=False
        )
        embed.set_footer(text='Thanks for using crimsoBOT!')

        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def servers(self, ctx):
        """List crimsoBOT's servers."""

        guilds = list(self.bot.guilds)
        await ctx.send(
            '**Connected on {} servers:**\n'.format(len(guilds)) +
            '\n'.join('`[{g.id}]` | {g.name}'.format(g=guild) for guild in guilds)
        )

    @commands.command(pass_context=True)
    async def serverinfo(self, ctx, server_id=None):
        """Member count, owner, channel names, roles, and emojis."""

        if server_id is None:
            guild = ctx.message.guild
        else:
            guild = self.bot.get_guild(server_id)

        embed = c.get_guild_info_embed(guild)

        # ...and send
        try:
            await ctx.send(embed=embed)
        except Exception:
            log.info("Guild info still too long, can't send...")

    @commands.command(pass_context=True, hidden=True)
    @checks.is_admin()
    async def save_from(self, ctx, server_id):
        """Pull crimsoBOT from a server."""

        guild = self.bot.get_guild(server_id)
        await guild.leave()
        log.info('crimsoBOT REMOVED from %s [%s]', guild, guild.id)

    @commands.command(hidden=True)
    @checks.is_admin()
    async def reload(self, ctx: commands.Context) -> None:
        """Reload all extensions. Intended for local development."""

        self.bot.reload_extensions()
        log.info('All extensions have been reloaded.')


def setup(bot):
    bot.add_cog(Admin(bot))
