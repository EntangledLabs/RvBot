import re
import asyncio

from discord.ext import commands
import discord

import permissions

class Competition:

    def __init__(self, bot: commands.Bot, perms: permissions.Permissions, guild: discord.Guild, boxes: list[str]):
        self.bot = bot
        self.perms = perms
        self.guild = guild

        self.boxes = boxes

    @commands.command()
    def box(self, ctx, *args):
        pass