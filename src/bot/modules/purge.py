from bot.module import *
import humanfriendly
import datetime

TIME_PERIODS = {"m": 60, "minute": 60, "minutes": 60, "h": 3600, "hour": 3600, "hours": 3600, "d": 86400, "day": 86400, "days": 86400}


class PurgeCommand(Module):

    def __init__(self, instance):
        super().__init__(instance, "purge")

    @add_command(brief="Purges messages", description="Purges messages. Examples: '!purge 1 hour', '!purge 2 days'")
    async def purge(self, ctx, num: int, time_string: str):
        if not ctx.channel.permissions_for(ctx.author).administrator:
            await ctx.send("You must be an administrator to do this")
            return
        if time_string not in TIME_PERIODS:
            await ctx.send("{} isn't a valid time period".format(time_string))
            return
        seconds = num * TIME_PERIODS[time_string]
        if seconds > 3 * 24 * 60 * 60:
            await ctx.send("Maximum purge length is 3 days")
            return
        confirm_message = "{}: Are you sure you want to purge messages sent in the last {}?".format(ctx.author.mention, humanfriendly.format_timespan(seconds))
        if await self.confirm(ctx, confirm_message):
            await ctx.send("Purging")
            start_time = datetime.datetime.now() - datetime.timedelta(seconds=seconds)

            async def messages_left():
                async for m in ctx.channel.history(limit=1):
                    return m.created_at > start_time
                return False

            with ctx.channel.typing():
                while await messages_left():
                    await ctx.channel.purge(limit=1000, after=start_time)

            await ctx.send("{}: successfully purged all messages sent in the last {}".format(ctx.author.mention, humanfriendly.format_timespan(seconds)))
        else:
            await ctx.send("Cancelled purge")

    @add_command(brief="Purges messages from one user", description="Purges messages. Examples: '!purgeuser @user 1 hour', '!purgeuser @user 2 days'")
    async def purgeuser(self, ctx, user: discord.Member, num: int, time_string: str):
        if not ctx.channel.permissions_for(ctx.author).administrator:
            await ctx.send("You must be an administrator to do this")
            return
        if ctx.channel.permissions_for(user).administrator and user != self.bot.user:
            await ctx.send("The messages of an administrator can not be deleted")
            return
        if time_string not in TIME_PERIODS:
            await ctx.send("{} isn't a valid time period".format(time_string))
            return
        seconds = num * TIME_PERIODS[time_string]
        if seconds > 31 * 24 * 60 * 60:
            await ctx.send("Maximum purge user length is 31 days")
            return
        confirm_message = "{}: Are you sure you want to purge messages sent by {} in the last {}?".format(ctx.author.mention, user.mention, humanfriendly.format_timespan(seconds))
        if await self.confirm(ctx, confirm_message):
            await ctx.send("Purging")
            start_time = datetime.datetime.now() - datetime.timedelta(seconds=seconds)

            def check_message(message):
                return message.author == user

            await ctx.channel.purge(limit=10000, after=start_time, check=check_message)

            await ctx.send("{}: successfully purged all messages sent by {} in the last {}".format(ctx.author.mention, user.mention, humanfriendly.format_timespan(seconds)))
        else:
            await ctx.send("Cancelled purge of {}'s messages".format(user.mention))
