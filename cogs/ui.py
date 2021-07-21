from datetime import timedelta
from urllib.parse import urlparse

import discord
from discord.ext import commands
from utils import ask_message, ask_reaction
import aiohttp
import asyncio


class ui(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.command(name='list', aliases=['scoreboards', 'sbs', 'list_scoreboards'])
    async def list_scoreboards(self, ctx):
        embed = discord.Embed()
        sbs = [sb for sb in self.bot.scoreboards if sb.guild.id == ctx.guild.id]
        
        if sbs:
            
            embed.title = f"This guild has {str(len(sbs))} scoreboards."
            embed.description = ""
            
            for i, sb in enumerate(sbs):

                channel = sb.channel
                if channel: channel = "in " + channel.mention
                else: channel = "No channel ⚠️"
                
                message = sb.message
                if message: jump = f"[Jump to message]({message.jump_url})"
                else: jump = "No message ⚠️"
                
                tab = " ".join(["\u200E"]*6)
                embed.description += f'**#{str(i+1)}** | {sb.name} (`{sb._message_id}`)\n{tab} | {channel} -> {jump}\n'

        else:
            embed.title = "This guild doesn't have any scoreboards yet!"
            embed.description = f"You can create one by typing `{ctx.prefix}create`."

        await ctx.send(embed=embed)

    async def ask_name(self, ctx, author='Creating new scoreboard... (1/7)'):
        embed = discord.Embed(color=discord.Color.from_rgb(66, 66, 66))
        embed.set_author(name=author)
        embed.add_field(name="What should the scoreboard's name be?", value="Keep it short. 32 characters max.")
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        name = await ask_message(ctx, embed=embed)
        if name == None: return
        elif name.lower() == "cancel": return
        def validate_name():
            if len(name) < 1 or len(name) > 32: return f"Invalid length! 32 characters max, you have {len(name)}."
            else: return None
        error = validate_name()
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(105, 105, 105))
            embed.set_author(name=error)
            name = await ask_message(ctx, embed)
            if name == None: return
            elif name.lower() == "cancel": return
            error = validate_name()
        return name
    async def ask_channel_id(self, ctx, author='Creating new scoreboard... (2/7)'):
        embed = discord.Embed(color=discord.Color.from_rgb(66, 66, 66))
        embed.set_author(name=author)
        embed.add_field(name="What channel should the scoreboard be in?", value="Must be a text channel the bot can send messages to.")
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        channel_id = await ask_message(ctx, embed=embed)
        if channel_id == None: return
        elif channel_id.lower() == "cancel": return
        async def validate_channel_id(channel_id):
            try: channel = await commands.TextChannelConverter().convert(ctx, channel_id)
            except commands.BadArgument as e: return str(e), None
            if not channel.permissions_for(ctx.guild.me).send_messages:
                return 'Can not send messages in that channel', None
            channel_id = channel.id
            return None, channel_id
        error, channel_id = await validate_channel_id(channel_id)
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(105, 105, 105))
            embed.set_author(name=error)
            channel_id = await ask_message(ctx, embed)
            if channel_id == None: return
            elif channel_id.lower() == "cancel": return
            error, channel_id = await validate_channel_id(channel_id)
        return channel_id
    async def ask_api_url(self, ctx, author='Creating new scoreboard... (3/7)'):
        embed = discord.Embed(color=discord.Color.from_rgb(66, 66, 66))
        embed.set_author(name=author)
        embed.add_field(name="What is the link to the Community RCON API?", value="I will retrieve my data through the API provided by the [Community RCON](https://github.com/MarechJ/hll_rcon_tool). A valid URL should look like either `http://<ipaddress>:<port>/api/` or `https://<hostname>/api/`.")
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        api_url = await ask_message(ctx, embed=embed)
        if api_url == None: return
        elif api_url.lower() == "cancel": return
        async def validate_api_url(api_url):
            if len(api_url) < 1 or len(api_url) > 200:
                return f"Invalid length! 200 characters max, you have {len(api_url)}.", None
            url = urlparse(api_url)
            if not url.scheme:
                return 'URL has no scheme, must be either http or https.', None
            url = url._replace(path='/api/')
            url = url._replace(params='')
            url = url._replace(query='')
            url = url._replace(fragment='')
            api_url = url.geturl()
            try:
                jar = aiohttp.CookieJar(unsafe=True)
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(cookie_jar=jar, timeout=timeout) as session:
                    async with session.get(api_url+'public_info') as res:
                        res = (await res.json())['result']
            except aiohttp.ContentTypeError as e:
                error = f'Webpage returned unexpected data. Likely the URL used ({api_url}) is incorrect.', None
            except asyncio.TimeoutError as e:
                error = f'Could not resolve host within 10 seconds. Check if the URL is correct ({api_url}) and the RCON tool is running.', None
            except KeyError:
                return 'Connected, but received unexpected data', None
            except Exception as e:
                return e.__class__.__name__ + ": " + str(e), None
            return None, api_url
        error, api_url = await validate_api_url(api_url)
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(105, 105, 105))
            embed.set_author(name=error)
            api_url = await ask_message(ctx, embed)
            if api_url == None: return
            elif api_url.lower() == "cancel": return
            if not api_url.endswith('/'): api_url = api_url + '/'
            if not api_url.endswith('api/'): api_url = api_url + 'api/'
            if not api_url.startswith('http://') or not api_url.startswith('https://'): api_url = 'http://' + api_url
            error, api_url = await validate_api_url(api_url)
        return api_url
    async def ask_api_user(self, ctx, author='Creating new scoreboard... (4/7)'):
        embed = discord.Embed(color=discord.Color.from_rgb(66, 66, 66))
        embed.set_author(name=author)
        embed.add_field(name="What username should be used to log in to the C.RCON?", value="This is the username that you would use to log in.")
        embed.set_image(url='https://cdn.discordapp.com/attachments/790967581396828190/856254303524880414/unknown.png')
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        api_user = await ask_message(ctx, embed=embed)
        if api_user == None: return
        elif api_user.lower() == "cancel": return
        def validate_api_user():
            if len(api_user) < 1 or len(api_user) > 64: return f"Invalid length! 64 characters max, you have {len(api_user)}."
            else: return None
        error = validate_api_user()
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(105, 105, 105))
            embed.set_author(name=error)
            api_user = await ask_message(ctx, embed)
            if api_user == None: return
            elif api_user.lower() == "cancel": return
            error = validate_api_user()
        return api_user
    async def ask_api_pw(self, ctx, author='Creating new scoreboard... (5/7)'):
        embed = discord.Embed(color=discord.Color.from_rgb(66, 66, 66))
        embed.set_author(name=author)
        embed.add_field(name="What password should be used to log in to the C.RCON?", value="This is the password that you would use to log in.")
        embed.set_image(url='https://media.discordapp.net/attachments/790967581396828190/856254363323203584/unknown.png')
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        api_pw = await ask_message(ctx, embed=embed, censor=True)
        if api_pw == None: return
        elif api_pw.lower() == "cancel": return
        def validate_api_pw():
            if len(api_pw) < 1 or len(api_pw) > 64: return f"Invalid length! 64 characters max, you have {len(api_pw)}."
            else: return None
        error = validate_api_pw()
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(105, 105, 105))
            embed.set_author(name=error)
            api_pw = await ask_message(ctx, embed)
            if api_pw == None: return
            elif api_pw.lower() == "cancel": return
            error = validate_api_pw()
        return api_pw
    async def ask_scoreboard_url(self, ctx, author='Creating new scoreboard... (6/7)'):
        embed = discord.Embed(color=discord.Color.from_rgb(66, 66, 66))
        embed.set_author(name=author)
        embed.add_field(name="What link should be used to redirect to the C.RCON's live scores page?", value="The [Community RCON](https://github.com/MarechJ/hll_rcon_tool) has a public stats page. A valid URL should look like either `http://<ipaddress>:<port>/#` or `https://<hostname>/#`. This value is OPTIONAL, typing \"none\" will leave it empty.")
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        scoreboard_url = await ask_message(ctx, embed=embed)
        if scoreboard_url == None: return
        elif scoreboard_url.lower() == "cancel": return
        elif scoreboard_url.lower() == "none": scoreboard_url = ""
        def validate_scoreboard_url():
            if len(scoreboard_url) == 0: return
            elif len(scoreboard_url) > 200: return f"Invalid length! 200 characters max, you have {len(scoreboard_url)}."
        error = validate_scoreboard_url()
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(105, 105, 105))
            embed.set_author(name=error)
            scoreboard_url = await ask_message(ctx, embed)
            if scoreboard_url == None: return
            elif scoreboard_url.lower() == "cancel": return
            elif scoreboard_url.lower() == "none": scoreboard_url = ""
            error = validate_scoreboard_url()
        return scoreboard_url
    async def ask_server_id(self, ctx, author='Creating new scoreboard... (7/7)'):
        embed = discord.Embed(color=discord.Color.from_rgb(66, 66, 66))
        embed.set_author(name=author)
        embed.add_field(name="What is the server's ID?", value="Required when having multiple servers connected to the [Community RCON](https://github.com/MarechJ/hll_rcon_tool). Check the C.RCON's `.env` file. If only one server is connected this should just be 1.")
        embed.set_image(url="https://media.discordapp.net/attachments/790967581396828190/856262209372684288/unknown.png")
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        server_id = await ask_message(ctx, embed=embed)
        if server_id == None: return
        elif server_id.lower() == "cancel": return
        def validate_server_id():
            try: int(server_id)
            except: return "Value is not a number"
            if int(server_id) < 1: return f"Number out of range! Must be greater than 0."
        error = validate_server_id()
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(105, 105, 105))
            embed.set_author(name=error)
            server_id = await ask_message(ctx, embed)
            if server_id == None: return
            elif server_id.lower() == "cancel": return
            error = validate_server_id()
        server_id = int(server_id)
        return server_id

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.command(name='create', aliases=['create_sb', 'create_scoreboard', 'add', 'add_sb', 'add_scoreboard'])
    async def create_scoreboard(self, ctx):

        name = await self.ask_name(ctx)
        if name == None: return
        
        channel_id = await self.ask_channel_id(ctx)
        if channel_id == None: return
        
        api_url = await self.ask_api_url(ctx)
        if api_url == None: return
        
        api_user = await self.ask_api_user(ctx)
        if api_user == None: return
        
        api_pw = await self.ask_api_pw(ctx)
        if api_pw == None: return
        
        scoreboard_url = await self.ask_scoreboard_url(ctx)
        if scoreboard_url == None: return
        
        server_id = await self.ask_server_id(ctx)
        if server_id == None: return

        scoreboard = await ctx.bot.scoreboards.register(ctx.bot, name, ctx.guild.id, channel_id, 0, api_url, api_user, api_pw, scoreboard_url, server_id)

        embed = discord.Embed(
            color=discord.Color(7844437),
            description=f"[Jump to scoreboard]({scoreboard.message.jump_url})\n\nYou can change the configuration at any time, using the below command:```{ctx.prefix}set {scoreboard.message.id} <option> <new value>```\nAvailable options: name, channel, api_url, api_user, api_pw, scoreboard_url, server_id"
        )
        embed.set_author(name=f"Scoreboard created", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
        await ctx.send(embed=embed)
        await scoreboard.update()

    async def get_scoreboard(self, ctx, message, return_index=False):
        try: message = int(message)
        except ValueError:
            try: message = (await commands.MessageConverter().convert(ctx, message)).id
            except commands.BadArgument:
                raise commands.BadArgument('Message could not be found')
        
        sb, i = ctx.bot.scoreboards.get(message, return_index=True)
        if not sb or sb.guild.id != ctx.guild.id:
            raise commands.BadArgument('No scoreboard found with message id %s' % message)
        return (sb, i) if return_index else sb

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.command(name='delete', aliases=['delete_sb', 'delete_scoreboard', 'remove', 'remove_sb', 'remove_scoreboard'])
    async def delete_scoreboard(self, ctx, message):
        sb = await self.get_scoreboard(ctx, message)

        embed = discord.Embed(color=discord.Color.gold())
        embed.add_field(name=f"⚠️ Are you sure you want to delete \"{sb.name}\"?", value="This will delete the associated message.")
        options = {
            "<:yes:809149148356018256>": "Yes, delete the scoreboard",
            "<:no:808045512393621585>": "No, keep the scoreboard"
        }
        res = await ask_reaction(ctx, embed, options)
        
        if res == "<:yes:809149148356018256>":
            await ctx.bot.scoreboards.delete(message)
            embed = discord.Embed(color=discord.Color(7844437))
            embed.set_author(name=f"Scoreboard deleted", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
            await ctx.send(embed=embed)

    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.group(name='set', aliases=['edit', 'update', 'set_scoreboard', 'edit_scoreboard', 'update_scoreboard'], invoke_without_command=False)
    async def set_scoreboard(self, ctx, message, option: str):
        sb, sb_index = await self.get_scoreboard(ctx, message, return_index=True)
        option = option.lower()

        if option in ['name']:
            value = await self.ask_name(ctx, author="Editing scoreboard...")
            if value: sb.name = str(value)

        elif option in ['channel', 'channel_id']:
            value = await self.ask_channel_id(ctx, author="Editing scoreboard...")
            if value:
                await sb.message.delete()
                sb.channel = ctx.guild.get_channel(int(value))
                sb.message = await sb.channel.send(embed=discord.Embed(description='No! Don\'t look yet!'))

        elif option in ['api_url', 'api', 'api_link']:
            value = await self.ask_api_url(ctx, author="Editing scoreboard...")
            if value: sb.url = str(value)

        elif option in ['api_user', 'api_username', 'user', 'username']:
            value = await self.ask_api_user(ctx, author="Editing scoreboard...")
            if value: sb.username = str(value)

        elif option in ['api_pw', 'api_password', 'pw', 'password']:
            value = await self.ask_api_pw(ctx, author="Editing scoreboard...")
            if value:
                sb.password = str(value)
                value = '\*'*20

        elif option in ['scoreboard_url', 'scoreboard', 'gamescoreboard', 'gamescoreboard_url']:
            value = await self.ask_scoreboard_url(ctx, author="Editing scoreboard...")
            if value is not None: sb.scoreboard_url = str(value)

        elif option in ['server_id', 'server_filter', 'server']:
            value = await self.ask_server_id(ctx, author="Editing scoreboard...")
            if value: sb.server_filter = int(value)

        else:
            raise commands.BadArgument('%s isn\'t a valid option. Available options: name, channel, api_url, api_user, api_pw, scoreboard_url, server_id' % option)
        
        if not value:
            return

        sb.save()
        ctx.bot.scoreboards.set(sb_index, sb)
        embed = discord.Embed(color=discord.Color(7844437), description=f"New value is {value}")
        embed.set_author(name=f"{option} updated", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
        await ctx.send(embed=embed)
        await sb.update()

def setup(bot):
    bot.add_cog(ui(bot))