import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
import re
import math
from datetime import datetime
import json

from models import DBConnection

EMOJIS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
EMBED_ICON = 'https://media.discordapp.net/attachments/729998051288285256/791030109628399647/MiP_-5ea_400x400.png'

LOGIN_ENDPOINT = 'login'
MAP_HISTORY_ENDPOINT = 'get_map_history'
GET_LOGS_ENDPOINT = 'get_historical_logs'

ASCII_ART = """`                    __________                     
              _____/          \______              
             |                      ||             
             |   _      ___    _    ||             
             |  | \      |    | \   ||             
             |  |  |     |    |  |  ||             
             |  |_/      |    |_/   ||             
             |  | \      |    |     ||             
             |  |  \     |    |     ||             
             |  |   \.  _|_.  | .   ||             
             |                      ||             
             | {: <21}||             
             |                      ||             
             |______________________||             
                                                  `"""

MAPS = {
    "foy_warfare": "Foy",
    "stmariedumont_warfare": "SMDM",
    "hurtgenforest_warfare": "Hurtgen",
    "hurtgenforest_warfare_V2": "Hurtgen",
    "utahbeach_warfare": "Utah",
    "omahabeach_offensive_us": "Off. Omaha",
    "stmereeglise_warfare": "SME",
    "stmereeglise_offensive_ger": "Off. SME (Ger)",
    "foy_offensive_ger": "Off. Foy",
    "purpleheartlane_warfare": "PHL",
    "purpleheartlane_offensive_us": "Off. PHL",
    "hill400_warfare": "Hill 400",
    "hill400_offensive_US": "Off. Hill 400",
    "stmereeglise_offensive_us": "Off. SME (US)",
    "carentan_warfare": "Carentan",
    "carentan_offensive_us": "Off. Carentan",
    "hurtgenforest_offensive_ger": "Off. Hurtgen (Ger)",
    "hurtgenforest_offensive_US": "Off. Hurtgen (US)",
    "utahbeach_offensive_us": "Off. Utah (US)",
    "utahbeach_offensive_ger": "Off. Utah (GER)",
}

class VerificationError(Exception):
    pass
class RCONError(Exception):
    pass
class ContentTypeError(Exception):
    pass

class ScoreboardInstance:
    @classmethod
    async def create(cls, bot, name, guild_id, channel_id, message_id, api_url, api_user, api_pw, scoreboard_url, server_id):
        self = ScoreboardInstance()

        self.bot = bot
        self.name = name
        self.url = api_url
        self.username = api_user
        self.password = api_pw
        self.scoreboard_url = scoreboard_url
        self.server_filter = int(server_id)
        self.guild = self.bot.get_guild(int(guild_id))
        self.channel = self.guild.get_channel(int(channel_id))
        self._message_id = int(message_id)
        try: self.message = await self.channel.fetch_message(self._message_id)
        except discord.NotFound:
            await self._resend_message()

        #await self.message.clear_reactions()
        self.page = 1
        return self
    async def _resend_message(self):
        self.message = await self.channel.send(embed=discord.Embed(description='No! Don\'t look yet!'))
        if self._message_id:
            with DBConnection('data.db') as cur:
                cur.execute('UPDATE scoreboards SET message_id = ? WHERE channel_id = ? AND name = ? AND api_url = ? AND server_id = ?',
                    (self.message.id, self.channel.id, self.name, self.url, self.server_filter))
        else:
            self.add_to_database()
        self._message_id = self.message.id

    async def update(self):
        try:
            try: self.message = await self.channel.fetch_message(self._message_id)
            except discord.NotFound: await self._resend_message()
            await self._fetch_data()
            await self._update_embed()
        except Exception as e:
            try: await self.display_message(f'Failed to update scoreboard:\n{e.__class__.__name__}: {str(e)}\n\nContact an admin if this keeps occuring.')
            except Exception as e2: print('UpdateError:', e2.__class__.__name__ + ': ' + str(e2))
            raise e
        
    async def _fetch_data(self):
        # Get logs
        jar = aiohttp.CookieJar(unsafe=True)
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(cookie_jar=jar, timeout=timeout) as session:

            try:
                # Login
                payload = {'username': self.username, 'password': self.password}
                async with session.post(self.url+LOGIN_ENDPOINT, json=payload) as res:
                    raw_data = await res.json()
                    if raw_data['error']:
                        raise RCONError(raw_data['error'])
                    failed = raw_data['failed']
                    if failed is True:
                        raise VerificationError('Failed to login to the RCON. Check if the username and password are correct.')
                
                # Get match history
                async with session.get(self.url+MAP_HISTORY_ENDPOINT) as res:
                    raw_data = await res.json()
                    if raw_data['error']:
                        raise RCONError(raw_data['error'])
                    match_history = raw_data['result']
                    
                    match_info = match_history[0]
                    match_start_ts = match_info['start']
                    self.match_end = None

                    self.match_start = datetime.utcfromtimestamp(match_start_ts)
                    if (datetime.utcnow() - self.match_start).total_seconds() < 300:
                        match_info = match_history[1]
                        match_start_ts = match_info['start']
                        self.match_start = datetime.utcfromtimestamp(match_start_ts)
                        match_end_ts = match_info['end']
                        self.match_end = datetime.utcfromtimestamp(match_end_ts)

                    current_map = match_info['name'].replace('_RESTART', '')
                    try: self.current_map = MAPS[current_map]
                    except KeyError: self.current_map = current_map
                
                # Get logs
                payload = {'limit': 999999, 'log_type': 'KILL', 'from': str(self.match_start), 'server_filter': self.server_filter}
                if self.match_end: payload['till'] = str(self.match_end)
                async with session.get(self.url+GET_LOGS_ENDPOINT, params=payload) as res:
                    raw_data = await res.json()
                    if raw_data['error']:
                        raise RCONError(raw_data['error'])
                    logs = raw_data['result']

            except aiohttp.ContentTypeError as e:
                raise ContentTypeError("Webpage returned unexpected data. Likely the URL is incorrect.\n\nRaw data:\n" + str(e))
            except asyncio.TimeoutError as e:
                e.args = 'Could not resolve host within 10 seconds. Check if the URL is correct and the RCON tool is running.', 
        
        # Parse logs
        data = dict()
        for log in logs:
            killer = log['player_name']
            victim = log['player2_name']

            if log['type'] == 'KILL':
                # Kills
                try: data[killer][0] += 1
                except KeyError: data[killer] = [1, 0]
            # Deaths
            try: data[victim][1] += 1
            except KeyError: data[victim] = [0, 1]
        data = dict(sorted(data.items(), key=lambda item: item[1][0]*1000-item[1][1], reverse=True))
        self._data = data

    async def _update_embed(self):
        # Get number of pages
        total_pages = math.ceil(len(self._data)/30)
        _from = ((self.page - 1) * 30) + 1
        _to = self.page * 30
        # Does current page overflow?
        if 0 < total_pages < self.page:
            self.page = total_pages

        # Turn data into arrays
        data = [
            (i+1, k, v[0], v[1], round(v[0]/v[1], 2) if v[1] else 0.00)
            for i, (k, v) in enumerate(self._data.items())
            if i+1 >= _from and i+1 <= _to
        ]

        # Add empty rows
        if len(data) < 30:
            data = data + [('', '', '', '', '')]*(30-len(data))

        # Write output
        output = "RANK  NAME                      KILLS  DEATHS K/D   "
        for rank, name, kills, deaths, kd in data:
            output += "\n#{: <4} {: <25} {: <6} {: <6} {: <6}".format(rank, name.replace('`', ''), kills, deaths, kd)
        output = "`" + output + "`"

        # Create embed
        match_duration = int((datetime.utcnow() - self.match_start).total_seconds() / 60)
        embed = discord.Embed(description=output)
        if self.scoreboard_url: embed.description += f'\n[\> Click here for an extended view]({self.scoreboard_url})'
        if not self._data:
            # Cool ASCII art when no data
            if match_duration >= 15 and match_duration <= 30:
                embed.description = ASCII_ART.format(self.name[:21])
            else:
                embed.description = "`{: <51}\n{: <51}\n{: <51}`".format('','        There is no data to be displayed :(','')
        embed.set_author(icon_url=EMBED_ICON, name=self.name)

        # Set embed footer
        if self.match_end:
            match_ended = int((datetime.utcnow() - self.match_end).total_seconds() / 60)
            match_length = int((self.match_end - self.match_start).total_seconds() / 60)
            embed.set_footer(text=f"Match ended {match_ended} minutes ago. It lasted {match_length} minutes. Map was {self.current_map}.\nPage {str(self.page)}/{str(total_pages)} - react below to cycle pages.")
        else:
            embed.set_footer(text=f"Match started {match_duration} minutes ago. Map is {self.current_map}.\nPage {str(self.page)}/{str(total_pages)} - react below to cycle pages.")
        
        # Update embed
        try:
            await self.message.edit(embed=embed)
        except:
            print("Failed to update scoreboard:")
            print(embed.description)
            embed.description = "Failed to update the scoreboard\nCome back later"
            await self.message.edit(embed=discord.Embed())

        # Update reactions
        for i, emoji in enumerate(EMOJIS):
            if i+1 <= total_pages and emoji not in [str(reaction) for reaction in self.message.reactions]:
                await self.message.add_reaction(emoji)
            elif i+1 > total_pages and emoji in [str(reaction) for reaction in self.message.reactions]:
                await self.message.clear_reaction(emoji)

    async def display_message(self, message):
        lines = list()
        words = message.split(' ')
        line = words.pop(0)
        for word in words:
            if len(line) + len(word.split('\n', 1)[0]) <= 47:
                line = line + " " + word
            else:
                lines.append(line)
                line = word
            while '\n' in line:
                lines.append('')
                lines[-1], line = line.split('\n', 1)
        lines.append(line)
        
        lines = [''] + lines + ['']
        
        for i, line in enumerate(lines):
            if len(line) <= 47:
                line = line + (' ' * (47 - len(line)))
                lines[i] = line

        output = '`  ' + '  `\n`  '.join(lines) + '  `'

        # Create embed
        embed = discord.Embed(description=output)
        if self.scoreboard_url: embed.description += f'\n[\> Click here for an extended view]({self.scoreboard_url})'
        embed.set_author(icon_url=EMBED_ICON, name=self.name)
       
        # Update embed
        await self.message.edit(embed=embed)

    def add_to_database(self):
        with DBConnection('data.db') as cur:
            cur.execute('INSERT INTO scoreboards VALUES (?,?,?,?,?,?,?,?,?)', (self.name, self.guild.id, self.channel.id,
                self.message.id, self.url, self.username, self.password, self.scoreboard_url, self.server_filter))

    async def delete(self):
        with DBConnection('data.db') as cur:
            cur.execute('DELETE FROM scoreboards WHERE message_id = ?', (self.message.id,))
        await self.message.delete()
        self = None

    def save(self):
        with DBConnection('data.db') as cur:
            cur.execute('''UPDATE scoreboards SET name = ?, guild_id = ?, channel_id = ?, message_id = ?,
                api_url = ?, api_user = ?, api_pw = ?, scoreboard_url = ?, server_id = ? WHERE message_id = ?''', (
                    self.name, self.guild.id, self.channel.id, self.message.id, self.url, self.username,
                    self.password, self.scoreboard_url, self.server_filter, self._message_id))
        self._message_id = self.message.id

from collections.abc import Sequence

class ScoreboardList(Sequence):
    def __init__(self, initial_value: list = []):
        self.scoreboards = initial_value
        super().__init__()

    def __getitem__(self, i):
        return self.scoreboards[i]
    def __len__(self):
        return len(self.scoreboards)

    def add(self, instance: ScoreboardInstance):
        self.scoreboards.append(instance)
        return self.scoreboards

    async def register(self, *args, **kwargs):
        instance = await ScoreboardInstance.create(*args, **kwargs)
        self.add(instance)
        return instance
    
    async def delete(self, message_id: int):
        for i, sb in enumerate(self.scoreboards):
            if sb.message.id == int(message_id):
                await sb.delete()
                self.scoreboards[i] = None
                return
        raise KeyError('No scoreboard found with this message_id')
    
    async def update_all(self, silent=True):
        for inst in self.scoreboards:
            try:
                if inst: await inst.update()
            except Exception as e:
                if not silent:
                    print('%s - Failed to update %s:\n%s' % (datetime.now(), inst.name, e))
        
    def get(self, message_id: int, return_index=False):
        result = None
        index = None
        for i, sb in enumerate(self):
            if not sb:
                continue
            elif sb.message.id == int(message_id):
                result = sb
                index = i
                break
        if return_index: return result, index
        else: return result
    
    def set(self, index, sb):
        self.scoreboards[index] = sb


class scoreboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with DBConnection('data.db') as con:
            con.execute('''CREATE TABLE IF NOT EXISTS scoreboards
                (name TEXT, guild_id INT, channel_id INT, message_id INT PRIMARY KEY, api_url TEXT, api_user TEXT, api_pw TEXT, scoreboard_url TEXT, server_id INT)''')

    @commands.Cog.listener()
    async def on_ready(self):
        
        with DBConnection('data.db') as cur:
            cur.execute('SELECT * FROM scoreboards')
            res = cur.fetchall()

        self.bot.scoreboards = ScoreboardList()
        for row in res:
            await self.bot.scoreboards.register(self.bot, *row)
        
        print('Launched at', datetime.now())     
        self.update_scoreboard.add_exception_type(Exception)
        self.update_scoreboard.start()


    @tasks.loop(minutes=1)
    async def update_scoreboard(self):
        await self.bot.scoreboards.update_all(silent=False)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        for scoreboard in self.bot.scoreboards:
            if payload.message_id == scoreboard.message.id and payload.user_id != self.bot.user.id:
                if str(payload.emoji) in EMOJIS:
                    new_page = EMOJIS.index(str(payload.emoji))+1
                    if scoreboard.page != new_page:
                        scoreboard.page = new_page
                        await scoreboard._update_embed()
                await scoreboard.message.remove_reaction(str(payload.emoji), payload.member)



        

def setup(bot):
    bot.add_cog(scoreboard(bot))