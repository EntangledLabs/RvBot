from discord.ext import commands

class Permissions:

    def __init__(self):
        self.directors = []
        self.green_team = []
        self.red_team = []

        self.dir_role = 'Director'
        self.gt_role = 'Green Team'
        self.rt_role = 'Red Team'

    def is_admin(self, ctx):
        author = ctx.author
        return False

    def is_competitor(self, ctx):
        author = ctx.author
        return False

    def perms_check(self):
        def predicate(ctx):
            return self.is_admin(ctx) and self.is_competitor(ctx)
        return commands.check(predicate)