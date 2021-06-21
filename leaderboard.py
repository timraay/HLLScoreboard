import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from datetime import datetime, timedelta
from io import StringIO

LOGIN_ENDPOINT = '/api/login'
GET_LOGS_ENDPOINT = '/api/get_historical_logs'

with open('creds.txt', 'r') as f:
    USERNAME, PASSWORD = f.read().split('\n')

RESET_ON_DAYS = [1, 16]

EMBED_ICON = 'https://media.discordapp.net/attachments/729998051288285256/791030109628399647/MiP_-5ea_400x400.png'


def next_update():
    now = datetime.now() - timedelta(hours=1)
    if now.day > 16 or (now.day == 16 and now.hour >= 12):
        exec_at = (now.replace(day=1) + timedelta(days=32)).replace(day=1,hour=12,minute=0,second=0)
    elif now.day == 1 and now.hour < 12:
        exec_at = now.replace(day=1,hour=12,minute=0,second=0)
    else:
        exec_at = now.replace(day=16,hour=12,minute=0,second=0)
    return exec_at

def last_update():
    dt = next_update()
    dt -= timedelta(days=15)
    if dt.day != 1: dt = dt.replace(day=16)
    return dt


class LeaderboardInstance:
    @classmethod
    async def create(cls, bot, url, guild_id, channel_id, name, content, show_full_results=True):
        self = LeaderboardInstance()

        self.bot = bot
        self.name = name
        self.url = url
        self.guild = self.bot.get_guild(guild_id)
        self.channel = self.guild.get_channel(channel_id)
        self.content = content
        self.show_full_results = show_full_results

        return self

    async def print(self):
        # Get logs
        jar = aiohttp.CookieJar(unsafe=True)
        async with aiohttp.ClientSession(cookie_jar=jar) as session:
            # Login
            payload = {'username': USERNAME, 'password': PASSWORD}
            await session.post(self.url+LOGIN_ENDPOINT, json=payload)
            # Get logs
            payload = {'limit': 999999, 'log_type': 'KILL', 'from': str(last_update())}
            async with session.get(self.url+GET_LOGS_ENDPOINT, params=payload) as res:
                logs = (await res.json())['result']

        # Parse logs
        data = dict()
        for log in logs:
            killer = log['player_name']
            victim = log['player2_name']
            try: data[killer][0] += 1
            except KeyError: data[killer] = [1, 0, {"None": 0}]
            try: data[victim][1] += 1
            except KeyError: data[victim] = [0, 1, {"None": 0}]
            # Parse weapon used
            weapon = log['content'].split(' with ')[-1]
            if weapon == "None": weapon = "Tank/Arty"
            try: data[killer][2][weapon] += 1
            except KeyError: data[killer][2][weapon] = 1

        # Order logs
        data = dict(sorted(data.items(), key=lambda item: item[1][0]*1000-item[1][1], reverse=True))

        # Turn into file
        output = "RANK   NAME                      KILLS  DEATHS K/D    WEAPON"
        for i, (name, (kills, deaths, weapons)) in enumerate(data.items()):
            kd = round(kills/deaths, 2) if deaths else 0.00
            weapon = max(weapons, key=weapons.get)
            output += "\n#{: <5} {: <25} {: <6} {: <6} {: <6} {}({})".format(i+1, name, kills, deaths, kd, weapon, weapons[weapon])
        f = StringIO(output)
        f.seek(0)
        
        # Send results over discord
        embed = discord.Embed(title=f"🏆 Leaderboard from {last_update().strftime('%b %d')} to {next_update().strftime('%b %d')} 🏆", color=discord.Color.gold())
        embed.set_author(icon_url=EMBED_ICON, name=self.name)
        for i, (name, (kills, deaths, weapons)) in enumerate(data.items()):
            i += 1
            if i > 15: break
            elif i == 1: rank = "🥇"
            elif i == 2: rank = "🥈"
            elif i == 3: rank = "🥉"
            else: rank = "#"+str(i)
            if i <= 6: rank = '_ _\n' + rank
            kd = round(kills/deaths, 2) if deaths else 0.00
            weapon = max(weapons, key=weapons.get)
            embed.add_field(name=f"{rank} {name}", value=f"Kills: {str(kills)}\nDeaths: {str(deaths)}\nK/D Ratio: {str(kd)}\nWeapon: {weapon}({str(weapons[weapon])})")
        await self.channel.send(content=self.content, embed=embed)
        if self.show_full_results: await self.channel.send(file=discord.File(f, "full_results.txt"))
        




class leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        leaderboards = [
            #('http://62.171.172.221:8040', 618763306726981652, 666991815978909697, '[WTH] Public Server 1 & 2', '', False),
            ('http://62.171.172.221:8040', 695232527123742742, 790967581396828190, '[WTH] Public Server 1 & 2', '<@!425249228185534485>', True)
        ]
        self.leaderboards = []
        for leaderboard in leaderboards:
            inst = await LeaderboardInstance.create(self.bot, *leaderboard)
            self.leaderboards.append(inst)
        self.print_leaderboard.start()


    @tasks.loop(hours=24)
    async def print_leaderboard(self):
        if datetime.now().day not in RESET_ON_DAYS:
            return

        for lb in self.leaderboards:
            try: await lb.print()
            except Exception as e: print('Failed to print leaderboard %s: %s: %s' % (lb.name, e.__class__.__name__, e))
        
    @print_leaderboard.before_loop
    async def queue_start_task(self):
        delay = -1
        while delay < 0:
            exec_at = next_update()
            delay = (exec_at - datetime.now()).total_seconds()
            if delay < 0: await asyncio.sleep(3600)
        print(str(exec_at))
        print(delay)
        await asyncio.sleep(delay)
        


        

def setup(bot):
    bot.add_cog(leaderboard(bot))

"""
http://marech.fr:8040/api/get_historical_logs?limit=999999&log_type=KILL&from=2020-12-30T00:00:00.0
"""

if __name__ == '__main__':
    async def test():
        host = 'http://62.171.172.221:8040'
        jar = aiohttp.CookieJar(unsafe=True)
        async with aiohttp.ClientSession(cookie_jar=jar) as session:
            # Login
            payload = {'username': 'Abusify', 'password': 'abu2020WTH'}
            async with session.post(host+'/api/login', json=payload) as res:
                print("\nURL:", res.url)
                print("Status:", res.status)
                print("Response:", await res.text())
            await asyncio.sleep(1)
            # Get logs
            payload = {'limit': 10, 'log_type': 'KILL'}
            async with session.get(host+'/api/get_historical_logs', params=payload) as res:
                print("\nURL:", res.url)
                print("Status:", res.status)
                print("Response:", await res.json())
    asyncio.run(test())