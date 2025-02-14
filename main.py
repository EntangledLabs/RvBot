from dotenv import load_dotenv
import discord
from discord.ext import commands
from os import getenv
import csv, re
import asyncio
import tomllib
from io import TextIOWrapper, BytesIO, StringIO

load_dotenv(override=True)

# setup

with open('config.toml', 'rb') as cfg:
    config = tomllib.load(cfg)

token = getenv('TOKEN')
guild_id = config['guild']['guild_id']

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

gt_allowed = [config['roles']['gt_role'], config['roles']['dir_role']]
admin_allowed = ['Admin', config['roles']['dir_role']]

competitor_role_re = re.compile(r'^Team\s[a-zA-Z0-9]+$')

bot = commands.Bot(
    command_prefix='!rvbot ',
    intents=intents,
    activity=discord.Activity(
        name='SWIFT Competitions',
        type=discord.ActivityType.listening
    )
)

# ++++==== Helper Methods ====++++
def get_competitor_role(ctx: commands.Context):
    comp_role = None
    for role in ctx.author.roles:
        if competitor_role_re.match(role.name):
            comp_role = role.name

    if comp_role is None:
        comp_role = ctx.author.name

    return comp_role

# ++++==== Competition Configuration Commands ====++++
@bot.command(pass_context=True)
@commands.check_any(commands.has_any_role(*admin_allowed),
                    commands.has_guild_permissions(administrator=True))
async def init(ctx: commands.Context):
    """Creates a new category, associated channels, and roles for the competition specified in the config"""

    # Get the guild
    guild = discord.utils.get(bot.guilds, id=guild_id)

    # Getting Role models
    comp_role = discord.utils.get(guild.roles, name=config['roles']['competitor_role'])
    if comp_role is None:
        await guild.create_role(name=config['roles']['competitor_role'] , color=discord.Color.purple())
        comp_role = discord.utils.get(guild.roles, name=config['roles']['competitor_role'])

    dev_role = discord.utils.get(guild.roles, name=config['roles']['dev_role'])
    if dev_role is None:
        await guild.create_role(name=config['roles']['dev_role'] , color=discord.Color.gold())
        dev_role = discord.utils.get(guild.roles, name=config['roles']['dev_role'])

    gt_role = discord.utils.get(guild.roles, name=config['roles']['gt_role'])
    rt_role = discord.utils.get(guild.roles, name=config['roles']['rt_role'])
    dir_role = discord.utils.get(guild.roles, name=config['roles']['dir_role'])

    # Overrides
    gt_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        gt_role: discord.PermissionOverwrite(read_messages=True)
    }
    rt_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        rt_role: discord.PermissionOverwrite(read_messages=True)
    }

    dev_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        dev_role: discord.PermissionOverwrite(read_messages=True)
    }

    main_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        comp_role: discord.PermissionOverwrite(read_messages=True),
        dev_role: discord.PermissionOverwrite(read_messages=True),
        gt_role: discord.PermissionOverwrite(read_messages=True),
        rt_role: discord.PermissionOverwrite(read_messages=True),
        dir_role: discord.PermissionOverwrite(read_messages=True)
    }

    announcement_overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        gt_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        rt_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        dir_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    # Creating competition category
    comp_cat = discord.utils.get(guild.categories, name=config['competition']['category_name'])
    if comp_cat is None:
        await guild.create_category(name=config['competition']['category_name'], overwrites=main_overwrites)
        comp_cat = discord.utils.get(guild.categories, name=config['competition']['category_name'])

    # Getting green team category
    gt_cat = discord.utils.get(guild.categories, name=config['guild']['gt_cat_name'])
    rt_cat = discord.utils.get(guild.categories, name=config['guild']['rt_cat_name'])
    if gt_cat is None:
        await guild.create_category(name=config['guild']['gt_cat_name'], overwrites=gt_overwrites)
        gt_cat = discord.utils.get(guild.categories, name=config['guild']['gt_cat_name'])
    if rt_cat is None:
        await guild.create_category(name=config['guild']['rt_cat_name'], overwrites=rt_overwrites)
        rt_cat = discord.utils.get(guild.categories, name=config['guild']['rt_cat_name'])

    # Checking for GT/RT channels
    gt_alert_channel = discord.utils.get(gt_cat.text_channels, name=config['competition']['alert_channel'])
    if gt_alert_channel is None:
        await gt_cat.create_text_channel(name=config['competition']['alert_channel'])
        gt_alert_channel = discord.utils.get(gt_cat.text_channels, name=config['competition']['alert_channel'])

    gt_general_channel = discord.utils.get(gt_cat.channels, name='general')
    if gt_general_channel is None:
        await gt_cat.create_text_channel(name='general')
        gt_general_channel = discord.utils.get(gt_cat.channels, name='general')

    rt_general_channel = discord.utils.get(rt_cat.channels, name='general')
    if rt_general_channel is None:
        await rt_cat.create_text_channel(name='general')
        rt_general_channel = discord.utils.get(rt_cat.channels, name='general')

    # Creating competition channels
    announcement_channel = discord.utils.get(comp_cat.text_channels, name='announcements')
    if announcement_channel is None:
        await comp_cat.create_text_channel(name='announcements', overwrites=announcement_overwrites)
        announcement_channel = discord.utils.get(comp_cat.text_channels, name='announcements')

    general_channel = discord.utils.get(comp_cat.text_channels, name='general')
    if general_channel is None:
        await comp_cat.create_text_channel(name='general', overwrites=main_overwrites)
        general_channel = discord.utils.get(comp_cat.text_channels, name='general')

    general_vc_channel = discord.utils.get(comp_cat.voice_channels, name='General')
    if general_vc_channel is None:
        await comp_cat.create_voice_channel(name='General', overwrites=main_overwrites)
        general_vc_channel = discord.utils.get(comp_cat.voice_channels, name='General')

    dev_channel = discord.utils.get(comp_cat.text_channels, name='dev')
    if dev_channel is None:
        await comp_cat.create_text_channel(name='dev', overwrites=dev_overwrites)
        dev_channel = discord.utils.get(comp_cat.text_channels, name='dev')

    dev_vc_channel = discord.utils.get(comp_cat.voice_channels, name='Dev General')
    if dev_vc_channel is None:
        await comp_cat.create_voice_channel(name='Dev General', overwrites=dev_overwrites)
        dev_vc_channel = discord.utils.get(comp_cat.voice_channels, name='Dev General')

    # Sending confirmation message to the chat
    embed = discord.Embed()
    embed.title = 'Competition initialize'
    embed.description = f'Created all categories and roles necessary for competition \'{config['competition']['name']}\''
    await ctx.send(embed=embed)

@bot.command(pass_context=True)
@commands.check_any(commands.has_any_role(*admin_allowed),
                    commands.has_guild_permissions(administrator=True))
async def teardown(ctx: commands.Context):
    """Deletes all associated roles and channels for the competition"""

    # Get the guild
    guild = discord.utils.get(bot.guilds, id=guild_id)
    comp_cat = discord.utils.get(guild.categories, name=config['competition']['category_name'])
    for channel in comp_cat.channels:
        await channel.delete()

    await comp_cat.delete()

    comp_role = discord.utils.get(guild.roles, name=config['roles']['competitor_role'])
    await comp_role.delete()

    embed = discord.Embed()
    embed.title = 'Competition teardown'
    embed.description = f'Deleted category and roles for competition \'{config['competition']['name']}\''
    await ctx.send(embed=embed)

@bot.command(pass_context=True)
@commands.check_any(commands.has_any_role(*admin_allowed),
                    commands.has_guild_permissions(administrator=True))
async def create_teams(ctx):
    """
    Creates team roles and categories based on an attached csv file.
    The CSV file should have the following format:
    | team name | member 1 discord | member 2 discord | member 3 discord | member 4 discord |
    """

    guild = discord.utils.get(bot.guilds, id=guild_id)
    gt_alert_channel = discord.utils.get(
        discord.utils.get(guild.categories, name=config['guild']['gt_cat_name']).text_channels,
        name=config['competition']['alert_channel']
    )

    # Reading CSV file
    with TextIOWrapper(BytesIO(await ctx.message.attachments[0].read())) as f:
        csvreader = csv.reader(f)

        for row in csvreader:
            team_name = row.pop(0)

            team_role = await guild.create_role(name=f'Team {team_name}')
            team_overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                team_role: discord.PermissionOverwrite(read_messages=True),
                discord.utils.get(guild.roles, name=config['roles']['gt_role']): discord.PermissionOverwrite(read_messages=True)
            }

            team_cat = await guild.create_category(name=f'{config['competition']['name']} {team_name}', overwrites=team_overwrites)
            await team_cat.create_text_channel(name='competitor-chat', overwrites=team_overwrites)
            await team_cat.create_voice_channel(name='competitor-voice', overwrites=team_overwrites)

            for teammate in row:
                try:
                    member = discord.utils.get(guild.members, name=teammate)
                    roles = [
                        team_role,
                        discord.utils.get(guild.roles, name=config['roles']['competitor_role'])
                    ]
                    for role in roles:
                        await member.add_roles(role)
                except Exception:
                    embed = discord.Embed()
                    embed.title = 'Teams creation'
                    embed.description = f'Teammate with username \'{teammate}\' is not in the server! Please add them manually.'
                    await gt_alert_channel.send(embed=embed)

    embed = discord.Embed()
    embed.title = 'Teams creation'
    embed.description = 'All team channels and roles have been created.'
    await ctx.send(embed=embed)

@bot.command(pass_context=True)
@commands.check_any(commands.has_any_role(*admin_allowed),
                    commands.has_guild_permissions(administrator=True))
async def delete_teams(ctx):
    """Removes all team roles and categories"""

    guild = discord.utils.get(bot.guilds, id=guild_id)

    competitor_role_re = re.compile(r'^Team\s[a-zA-Z0-9]+$')
    competitor_cat_re = re.compile(fr'^{config['competition']['name']}\s[a-zA-Z0-9]+$')

    for role in guild.roles:
        if competitor_role_re.match(role.name) is not None:
            await role.delete()

    for category in guild.categories:
        if competitor_cat_re.match(category.name):
            for channel in category.channels:
                await channel.delete()
            await category.delete()

    embed = discord.Embed()
    embed.title = 'Teams deletion'
    embed.description = 'All team channels and roles have been deleted.'
    await ctx.send(embed=embed)

# ++++==== GT Helpers ====++++
@bot.command(pass_context=True)
@commands.check_any(commands.has_any_role(*[*gt_allowed, *admin_allowed]),
                    commands.has_guild_permissions(administrator=True))
async def send_creds(ctx):
    """Sends creds to the teams from an attached csv file"""

    embed = discord.Embed()
    embed.title = 'Credential Sender'

    guild = discord.utils.get(bot.guilds, id=guild_id)
    with TextIOWrapper(BytesIO(await ctx.message.attachments[0].read())) as f:
        csvreader = csv.reader(f)

        for row in csvreader:
            team_name = row.pop(0)
            team_role = await discord.utils.get(guild.roles, name=f'Team {team_name}')
            team_cat = await discord.utils.get(guild.categories, name=f'{config['competition']['name']} {team_name}')
            team_general = await discord.utils.get(team_cat.text_channels, name='competitor-chat')

            embed.description = f'Your credentials are: {row.pop(0)}:{row.pop(0)}'
            team_general.send(embed=embed)


# ++++==== GT Support ====++++
@bot.command(pass_context=True)
@commands.check_any(commands.has_any_role(*[*gt_allowed, config['roles']['competitor_role']]),
                    commands.has_guild_permissions(administrator=True))
async def support(ctx: commands.Context):
    """
    Requests Green Team support. Command format is:
    !rvbot support
    """

    comp_role = get_competitor_role(ctx)
    guild = discord.utils.get(bot.guilds, id=guild_id)
    gt_alert_channel = discord.utils.get(
        discord.utils.get(guild.categories, name=config['guild']['gt_cat_name']).text_channels,
        name=config['competition']['alert_channel']
    )
    gt_role = discord.utils.get(guild.roles, name=config['roles']['gt_role'])

    gt_embed = discord.Embed()
    gt_embed.title = 'Green Team Support Request'
    gt_embed.description = f'{gt_role.mention} Support request for **{comp_role}**! -> {ctx.channel.mention}'

    competitor_embed = discord.Embed()
    competitor_embed.title = 'Green Team Support Request Received'
    competitor_embed.description = 'Support request sent! A Green Team member will be with you ASAP'

    await gt_alert_channel.send(embed=gt_embed)
    await ctx.send(embed=competitor_embed)

@bot.command(pass_context=True)
@commands.check_any(commands.has_any_role(*[*gt_allowed, config['roles']['competitor_role']]),
                    commands.has_guild_permissions(administrator=True))
async def reset(ctx, *args):
    """
    Requests a box reset. Command format is:
    !rvbot reset <box name>
    """

    comp_role = get_competitor_role(ctx)
    guild = discord.utils.get(bot.guilds, id=guild_id)
    gt_alert_channel = discord.utils.get(
        discord.utils.get(guild.categories, name=config['guild']['gt_cat_name']).text_channels,
        name=config['competition']['alert_channel']
    )
    gt_role = discord.utils.get(guild.roles, name=config['roles']['gt_role'])

    embed = discord.Embed()
    embed.title = 'Box Reset Wizard'

    if args[0] not in config['competition']['boxes']:
        embed.description = f'The box you specified, **{args[0]}**, does not exist!'
        await ctx.send(embed=embed)
    else:
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        embed.description = f'Please confirm that you want to request a box reset for **{args[0]}**! This CANNOT be undone. (y/n)'
        await ctx.send(embed=embed)

        try:
            response = await bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            embed.description = 'Timeout! Request expired, please run the command again'
            await ctx.send(embed=embed)
            return

        if response.content.lower() in ('yes', 'y'):
            embed.description ='Box reset request sent! Please hang tight.'
            await ctx.send(embed=embed)

            embed.description = f'{gt_role.mention} Box reset request! **{comp_role}** would like a reset on **{args[0]}**'
            await gt_alert_channel.send(embed=embed)
        else:
            embed.description = 'Box reset request cancelled!'
            await ctx.send(embed=embed)

# Main bot start
if __name__ == '__main__':
    bot.run(token=token)