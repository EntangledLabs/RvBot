# Green competitor support commands
@bot.command(pass_context=True)
@commands.check_any(commands.has_role(f'{Settings.get_setting('comp_name')} Competitor'),
                    commands.has_role("Green Team"),
                    commands.has_role("Director"),
                    commands.has_guild_permissions(administrator=True))
async def request(ctx: commands.context.Context, *args):
    log.info('Command \'request\' invoked. Someone has a GT request.')
    guild = discord.utils.get(bot.guilds, id=guild_id)
    gt_alert_channel = discord.utils.get(guild.text_channels, name='green-competitor-alert')
    gt_role = discord.utils.get(guild.roles, name='Green Team')
    competitor_role_re = re.compile(r'^Team\s[a-zA-Z0-9]+$')
    for role in ctx.author.roles:
        if competitor_role_re.match(role.name):
            comp_role = role.name

    if comp_role is None:
        comp_role = ctx.author.name

    if args[0] == 'support':
        await gt_alert_channel.send(f'{gt_role.mention} Support request for **{comp_role}**! -> {ctx.channel.mention}')
        await ctx.send('Support request sent! A Green Team member will be with you ASAP')

    elif args[0] == 'reset':
        box_names = [box.name for box in Box.find_all()]
        if args[1] not in box_names:
            await ctx.send(f'The box you specified, **{args[1]}**, does not exist!')
        else:
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            await ctx.send(
                f'Please confirm that you want to request a box reset for **{args[1]}**! This CANNOT be undone. (y/n)')

            try:
                response = await bot.wait_for('message', check=check, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send('Timeout! Request expired, please run the command again')
                return

            if response.content.lower() in ('yes', 'y'):
                await ctx.send('Box reset request sent! Please hang tight.')
                await gt_alert_channel.send(
                    f'{gt_role.mention} Box reset request! **{comp_role}** would like a reset on **{args[1]}**')
            else:
                await ctx.send('Box reset request cancelled!')