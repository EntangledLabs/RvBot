import re
import asyncio

from discord.ext import commands
import discord

import permissions, competition

class Support(commands.Cog):

    def __init__(self, bot: commands.Bot, perms: permissions.Permissions, guild: discord.Guild, comp: competition.Competition):
        self.bot = bot
        self.perms = perms
        self.guild = guild
        self.comp = comp

        self.gt_alert_channel = discord.utils.get(self.guild.text_channels, name='green-competitor-alert')
        self.gt_role = discord.utils.get(self.guild.roles, name='Green Team')
        self.competitor_role_re = re.compile(r'^Team\s[a-zA-Z0-9]+$')

    def get_competitor_role(self, ctx):
        comp_role = None
        for role in ctx.author.roles:
            if self.competitor_role_re.match(role.name):
                comp_role = role.name

        if comp_role is None:
            comp_role = ctx.author.name

        return comp_role

    @commands.command()
    async def support(self, ctx):
        comp_role = self.get_competitor_role(ctx)

        await self.gt_alert_channel.send(f'{self.gt_role.mention} Support request for **{comp_role}**! -> {ctx.channel.mention}')
        await ctx.send('Support request sent! A Green Team member will be with you ASAP')

    @commands.command()
    async def reset(self, ctx, *args):
        comp_role = self.get_competitor_role(ctx)

        box_names = self.comp.boxes
        if args[0] not in box_names:
            await ctx.send(f'The box you specified, **{args[0]}**, does not exist!')
        else:
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            await ctx.send(
                f'Please confirm that you want to request a box reset for **{args[0]}**! This CANNOT be undone. (y/n)')

            try:
                response = await self.bot.wait_for('message', check=check, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send('Timeout! Request expired, please run the command again')
                return

            if response.content.lower() in ('yes', 'y'):
                await ctx.send('Box reset request sent! Please hang tight.')
                await self.gt_alert_channel.send(
                    f'{self.gt_role.mention} Box reset request! **{comp_role}** would like a reset on **{args[0]}**')
            else:
                await ctx.send('Box reset request cancelled!')