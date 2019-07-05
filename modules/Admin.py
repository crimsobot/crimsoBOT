import discord
from discord.ext import commands
import os
from .clib import crimsotools as c

# path to root
root_dir = os.path.dirname(__file__) #<-- absolute dir the script is in

class Admin:
    def __init__(self,bot):
        self.bot = bot

    @commands.command(pass_context=True, hidden=True)
    async def ban(self, ctx, user_mention):
        """Ban user from using crimsoBOT."""
        if ctx.message.author.id != '310618614497804289':
            return
        if (ctx.message.mentions.__len__() == 1):
            for user in ctx.message.mentions:
                discord_user_object = user
        if discord_user_object.id == '310618614497804289':
            return
        c.ban(discord_user_object.id)
        embed = c.crimbed(None, '**{u.name}#{u.discriminator}** has been banned from using crimsoBOT.'.format(u=discord_user_object), None)
        msg = await self.bot.say(embed=embed)
        await self.bot.add_reaction(msg, '👺')

    @commands.command(pass_context=True, hidden=True)
    async def unban(self, ctx, user_mention):
        """Ban user from using crimsoBOT."""
        if ctx.message.author.id != '310618614497804289':
            return
        if (ctx.message.mentions.__len__() == 1):
            for user in ctx.message.mentions:
                discord_user_object = user
        c.unban(discord_user_object.id)
        embed = c.crimbed(None, '**{u.name}#{u.discriminator}** has been unbanned from using crimsoBOT.'.format(u=discord_user_object), None)
        msg = await self.bot.say(embed=embed)
        await self.bot.add_reaction(msg, '🛐')

    @commands.command(pass_context=True, hidden=True)
    async def banlist(self, ctx):
        """List of banned users."""
        cb_user_object_list = c.who_is_banned()
        banned_users = []
        for user in cb_user_object_list:
            discord_user_object = await self.bot.get_user_info(user.ID)
            banned_users.append('· {u.name}#{u.discriminator}'.format(u=discord_user_object))
        # number_of_banned_users = len(banned_users)
        msg_string = '\n'.join(banned_users)
        msg_list = c.crimsplit(msg_string, '\n', limit=1990)
        for msg in msg_list:
            await self.bot.say('```{}```'.format(msg))

    @commands.command(pass_context=True)
    async def info(self, ctx):
        """crimsoBOT info and invites."""
        title = 'crimsoBOT info'
        descr = 'crimsoBOT is a poorly-coded, homebrew bot that\'s hosted (at the moment) on crimso\'s laptop.\n'
        thumb = 'https://i.imgur.com/9UTNIGi.png'
        embed = c.crimbed(title, descr, thumb)
        embed.add_field(name='crimsoBOT\'s Discord server', value='https://discord.gg/Kj3WNHX', inline=False)
        embed.add_field(name='Invite crimsoBOT to your server', value='https://discordapp.com/api/oauth2/authorize?client_id=552650993595318282&permissions=473300048&scope=bot', inline=False)
        embed.add_field(name='Support crimsoBOT and get stickers!', value='https://www.patreon.com/crimso', inline=False)
        embed.set_footer(text='Thanks for using crimsoBOT!')
        await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.command(pass_context=True)
    async def servers(self, ctx):
        """List crimsoBOT's servers."""
        servers = list(self.bot.servers)
        await self.bot.say(f'**Connected on {str(len(servers))} servers:**\n' + '\n'.join('`[{s.id}]` | {s.name}'.format(s=server) for server in servers))
    
    @commands.command(pass_context=True)
    async def serverinfo(self, ctx, server_id=None):
        """Member count, owner, channel names, roles, and emojis."""
        if server_id is None:
            server = ctx.message.server
        else:
            server = self.bot.get_server(server_id)
        # initialize embed 
        embed = discord.Embed(title = 'serverinfo: {}'.format(server.name),
                              description = '`{}` members // owner: `{}`'.format(len(server.members), server.owner),
                              color = 0x5CC23E)
        # channels (up to 10)
        channel_list = [x for x in sorted(server.channels, key=lambda c: c.position) if x.type == discord.ChannelType.text]
        show = min(10, len(server.channels))
        embed.add_field(name = 'Channels ({}/{} shown)'.format(show, len(server.channels)),
                        value = '\n'.join([('· {}'.format(channel.name)) for channel in channel_list[:show]]) or 'No channels.',
                        inline = False)
        # roles (sans @everyone), up to 10
        role_list = [x for x in sorted(server.roles, key=lambda r: r.position, reverse=True) if not x.is_everyone]
        show = min(10, len(role_list))
        # role_list = [x for x in server.roles if not x.is_everyone][0:10]
        embed.add_field(name = 'Roles ({}/{} shown)'.format(show, len(server.roles)-1), # minus 1 to not include @everyone
                        value = '\n'.join(['· {}{}'.format('@' if role.mentionable else '', role.name) for role in role_list[:show]]) or 'No roles.',
                        inline = False)
        # emojis; truncate until names to be displayed sum to <500 characters
        total = len(server.emojis)
        char_count = sum([len(emoji.name) for emoji in server.emojis])
        while char_count > 500:
            server.emojis = server.emojis[:-1]
            show = len(server.emojis)
            char_count = sum([len(emoji.name) for emoji in server.emojis])
        embed.add_field(name = 'Emojis ({}/{} shown)'.format(len(server.emojis), total),
                        value = ' '.join(['`:{}:`'.format(emoji.name) for emoji in server.emojis]) or 'No custom emojis.',
                        inline = False)
        # footer, thumbnail
        embed.set_footer(text = 'Server ID: #{}'.format(server.id))
        embed.set_thumbnail(url = server.icon_url)
        # ...and send
        try:
            await self.bot.send_message(ctx.message.channel, embed=embed)
        except:
            print('Too long still!')
    
    @commands.command(pass_context=True, hidden=True)
    async def save_from(self, ctx, server_id):
        """Pull crimsoBOT from a server."""
        if ctx.message.author.id =='310618614497804289':
            server = self.bot.get_server(server_id)
            await self.bot.leave_server(server)
            c.botlog('crimsoBOT REMOVED from {server} [{server.id}]'.format(server=server))
    
    @commands.command(pass_context=True, hidden=True)
    async def logs(self, ctx, n):
        if ctx.message.author.id =='310618614497804289':
            with open(root_dir+'\\ref\\botlog.txt', 'r', encoding='utf8', errors='ignore') as f:
                msg = f.readlines()[-int(n):]
                msg = ''.join(msg)
            log_msgs = c.crimsplit(msg, '\n', 1900)
            for msg in log_msgs:
                await self.bot.send_message(ctx.message.author,'```'+msg+'```')

def setup(bot):
    bot.add_cog(Admin(bot))