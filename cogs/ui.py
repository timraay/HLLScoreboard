from datetime import timedelta
from models import DBConnection
import discord
from discord.ext import commands
from utils import ask_message
import aiohttp

class ui(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='list', aliases=['scoreboards', 'sbs', 'list_scoreboards'])
    async def list_scoreboards(self, ctx):
        embed = discord.Embed()
        sbs = [sb for sb in self.bot.scoreboards if sb.guild_id == ctx.guild.id]
        
        if sbs:
            
            embed.title = f"This guild has {str(len(sbs))} scoreboards."
            embed.description = ""
            
            for i, sb in enumerate(sbs):

                channel = ctx.guild.get_channel(sb.channel_id)
                if channel: channel = channel.mention
                else: channel = "No channel ⚠️"
                
                try: message = await commands.MessageConverter().convert(ctx, f'{sbs.channel_id}-{sbs.message_id}')
                except commands.BadArgument: message = None
                if message: jump = f"[Jump to message]({message.jump_url})"
                else: jump = "No message ⚠️"
                
                embed.description += f'**#{str(i+1)}** | {sb.name} ({channel}) - \n{jump} - ID: `{sbs.message_id}`'

        else:
            embed.title = "This guild doesn't have any scoreboards yet!"
            embed.description = f"You can create one by typing `{ctx.prefix}create`."

        await ctx.send(embed=embed)

    @commands.command(name='create', aliases=['create_sb', 'create_scoreboard', 'add', 'add_sb', 'add_scoreboard'])
    async def create_scoreboard(self, ctx):
        # name
        embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
        embed.set_author(name="Creating new scoreboard... (1/7)")
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
            embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
            embed.set_author(name=error)
            name = await ask_message(ctx, embed)
            if name == None: return
            elif name.lower() == "cancel": return
            error = validate_name()
        
        # channel_id
        embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
        embed.set_author(name="Creating new scoreboard... (2/7)")
        embed.add_field(name="What channel should the scoreboard be in?", value="Must be a text channel the bot can send messages to.")
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        channel_id = await ask_message(ctx, embed=embed)
        if channel_id == None: return
        elif channel_id.lower() == "cancel": return
        async def validate_channel_id(channel_id):
            try: channel = await commands.TextChannelConverter().convert(ctx, channel_id)
            except commands.BadArgument as e: error = str(e)
            if not channel.permissions_for(ctx.guild.me).send_messages:
                return 'Can not send messages in that channel'
            channel_id = channel.id
        error = await validate_channel_id(channel_id)
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
            embed.set_author(name=error)
            channel_id = await ask_message(ctx, embed)
            if channel_id == None: return
            elif channel_id.lower() == "cancel": return
            error = await validate_channel_id(channel_id)

        # api_url
        embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
        embed.set_author(name="Creating new scoreboard... (3/7)")
        embed.add_field(name="What is the link to the Community RCON API?", value="I will retrieve my data from the API provided by the [Community RCON](https://github.com/MarechJ/hll_rcon_tool). A valid URL should look like either `http://<ipaddress>:<port>/api/` or `https://<hostname>/api/`.")
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        api_url = await ask_message(ctx, embed=embed)
        if api_url == None: return
        elif api_url.lower() == "cancel": return
        elif not api_url.endswith('/'): api_url += '/'
        async def validate_api_url():
            if len(api_url) < 1 or len(api_url) > 200: return f"Invalid length! 200 characters max, you have {len(api_url)}."
            try:
                jar = aiohttp.CookieJar(unsafe=True)
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(cookie_jar=jar, timeout=timeout) as session:
                    async with session.get(api_url+'public_info') as res:
                        res = (await res.json())['result']
            except KeyError:
                return 'Connected, but received unexpected data'
            except Exception as e:
                return str(e)
        error = await validate_api_url()
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
            embed.set_author(name=error)
            api_url = await ask_message(ctx, embed)
            if api_url == None: return
            elif api_url.lower() == "cancel": return
            error = await validate_api_url()

        # api_user
        embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
        embed.set_author(name="Creating new scoreboard... (4/7)")
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
            embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
            embed.set_author(name=error)
            api_user = await ask_message(ctx, embed)
            if api_user == None: return
            elif api_user.lower() == "cancel": return
            error = validate_api_user()

        # api_pw
        embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
        embed.set_author(name="Creating new scoreboard... (5/7)")
        embed.add_field(name="What password should be used to log in to the C.RCON?", value="This is the password that you would use to log in.")
        embed.set_image(url='https://media.discordapp.net/attachments/790967581396828190/856254363323203584/unknown.png')
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        api_pw = await ask_message(ctx, embed=embed)
        if api_pw == None: return
        elif api_pw.lower() == "cancel": return
        def validate_api_pw():
            if len(api_pw) < 1 or len(api_pw) > 64: return f"Invalid length! 64 characters max, you have {len(api_pw)}."
            else: return None
        error = validate_api_pw()
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
            embed.set_author(name=error)
            api_pw = await ask_message(ctx, embed)
            if api_pw == None: return
            elif api_pw.lower() == "cancel": return
            error = validate_api_pw()
      
        # scoreboard_url
        embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
        embed.set_author(name="Creating new scoreboard... (6/7)")
        embed.add_field(name="What link should be used to redirect to the C.RCON's gamescoreboard page?", value="The [Community RCON](https://github.com/MarechJ/hll_rcon_tool) has a public stats page. A valid URL should look like either `http://<ipaddress>:<port>/#/gamescoreboard` or `https://<hostname>/#/gamescoreboard`. This value is OPTIONAL, typing \"none\" will leave it empty.")
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        scoreboard_url = await ask_message(ctx, embed=embed)
        if scoreboard_url == None: return
        elif scoreboard_url.lower() == "cancel": return
        elif scoreboard_url.lower() == "none": scoreboard_url = ""
        def validate_scoreboard_url():
            if len(scoreboard_url) == 0: return
            elif len(scoreboard_url) > 200: return f"Invalid length! 200 characters max, you have {len(scoreboard_url)}."
            elif '#/gamescoreboard' not in scoreboard_url: return "URL doesn't contain \"#/gamescoreboard\""
        error = validate_scoreboard_url()
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
            embed.set_author(name=error)
            scoreboard_url = await ask_message(ctx, embed)
            if scoreboard_url == None: return
            elif scoreboard_url.lower() == "cancel": return
            elif scoreboard_url.lower() == "none": scoreboard_url = ""
            error = validate_scoreboard_url()

        # server_id
        embed = discord.Embed(color=discord.Color.from_rgb(122, 255, 149))
        embed.set_author(name="Creating new scoreboard... (7/7)")
        embed.add_field(name="What is the server's ID?", value="Required when having multiple servers connected to the [Community RCON](https://github.com/MarechJ/hll_rcon_tool). Check the C.RCON's `.env` file. If only one server is connected this should just be 1.")
        embed.set_image(url="https://media.discordapp.net/attachments/790967581396828190/856262209372684288/unknown.png")
        embed.set_footer(text="Type \"cancel\" to cancel the creation process")
        server_id = await ask_message(ctx, embed=embed)
        if server_id == None: return
        elif server_id.lower() == "cancel": return
        def validate_server_id():
            try: server_id = int(server_id)
            except: return "Value is not a number"
            if server_id < 1: return f"Number out of range! Must be greater than 0."
        error = await validate_server_id()
        while error is not None:
            embed = discord.Embed(color=discord.Color.from_rgb(255, 255, 254))
            embed.set_author(name=error)
            server_id = await ask_message(ctx, embed)
            if server_id == None: return
            elif server_id.lower() == "cancel": return
            error = validate_server_id()

        scoreboard = await ctx.bot.scoreboards.register(ctx.bot, name, ctx.guild.id, channel_id, 0, api_url, api_user, api_pw, scoreboard_url, server_id)

        embed = discord.Embed(
            color=discord.Color(7844437),
            description=f"[Jump to scoreboard]({scoreboard.message.jump_url})\n\nYou can change the configuration at any time, using the below command:```{ctx.prefix}set {scoreboard.message.id} <option> <new value>```\nAvailable options: name, channel, api_url, api_user, api_pw, scoreboard_url, server_id"
        )
        embed.set_author(name=f"Scoreboard created", icon_url="https://cdn.discordapp.com/emojis/809149148356018256.png")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(ui(bot))