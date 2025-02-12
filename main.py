from dotenv import load_dotenv
import discord
from discord.ext import commands
from os import getenv
import csv, re
from io import TextIOWrapper, BytesIO, StringIO

from gt.support import Support

from permissions import Permissions

load_dotenv(override=True)

# setup

token = getenv('TOKEN')
guild_id = int(getenv('GUILD_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

permissions = Permissions()

bot = commands.Bot(
    command_prefix='!rvbot ',
    intents=intents
)

guild = discord.utils.get(bot.guilds, id=guild_id)

# Main bot loop
if __name__ == '__main__':
    bot.add_cog(Support(bot, permissions, guild))

    bot.run(token=token)