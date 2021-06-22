# HLL Scoreboard: Live Hell Let Loose scoreboards in your Discord server.

<img align="right" width="260" height="260" src="icon.png">

HLL Scoreboard is a Discord bot made by timraay/Abusify that allows Hell Let Loose server owners to display current statistics in their Discord server. Statistics will be pulled from the [HLL Community RCON tool](https://github.com/MarechJ/hll_rcon_tool) by [MarechJ](https://github.com/MarechJ).

Invite and use the bot by [clicking here](https://discord.com/api/oauth2/authorize?client_id=811927151631794236&permissions=8&scope=bot)! If you want to use the code to run your own bot, see the conditions below.

### License
HLL Scoreboard has a GNU GPLv3 license. In short, you can obtain a copy of the source code, modify it, and even distribute it. When modifying the code though, you must keep the GNU GPLv3 license. Your software should also be marked as changed, with a reference to the original source code.

# Setup
You must be an administrator of the Discord server you are adding the scoreboard to.
1. Invite the bot to your server using [this link](https://discord.com/api/oauth2/authorize?client_id=811927151631794236&permissions=8&scope=bot)!
2. Run the `s!add` command (doesn't have to be in the channel you want the scoreboard in)
3. Follow the creation process. It will ask you for the following information, in the below order:
  - The name your scoreboard should be given
  - The channel your scoreboard should be in
  - A link to the Community RCON's API. To verify your link is correct, add `public_info` to the end (and possibly join the two with a `/`), and enter the link in your browser.
  - The username used to log in to the Community RCON. It is recommended to create a separate account for the bot to log in with.
  - The password used to log in. While the message will be immediately deleted upon entering, be careful that unwanted people do not catch a glimpse of it. I am not responsible for leaked credentials.
  - An optional link to the public gamescoreboard page from the Community RCON
  - The number your HLL server is given by the Community RCON, for filtering logs

## Running your own bot
In case you have cloned the code and are willing to run the bot yourself, there's a couple of things you have to do.
1. Install Python 3 if you haven't already
2. Navigate to the root folder of the code
3. Install the dependencies: `pip3 install -r requirements.txt`
4. Create a file called `token.txt` in the root folder and paste the token of [your Bot application](https://discord.com/developers/applications) there. Make sure there's no trailing spaces or newlines.
5. Run the code! `python3 bot.py`