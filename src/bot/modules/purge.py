from discord.ext.commands import BadArgument

from bot.module import *
import humanfriendly
import datetime


class PurgeCommand(Module):

    def __init__(self, instance):
        super().__init__(instance, "purge")

    @add_command(brief="Purges messages", description="Purges messages. Maximum purge length is 3 days. Examples: '!purge 1h', '!purge 2sec', '!purge 3days'")
    async def purge(self, ctx, time_period: humanfriendly.parse_timespan):
        if not ctx.channel.permissions_for(ctx.author).manage_messages:
            await ctx.send("You must have permissions to delete messages in the channel to do this")
            return
        if time_period > 3 * 24 * 60 * 60:
            raise BadArgument("Maximum purge length is 3 days")

        message = ctx.author.mention + ": {} all messages sent in the last " + humanfriendly.format_timespan(time_period) + "{}"
        await self._do_purge(ctx, time_period, message)

    @add_command(brief="Purges messages from one user", description="Purges messages from one user. Maximum length is 31 days. Examples: '!purgeuser @user 1hour', '!purgeuser @user 2days'")
    async def purgeuser(self, ctx, user: discord.Member, time_period: humanfriendly.parse_timespan):
        if not ctx.channel.permissions_for(ctx.author).manage_messages:
            await ctx.send("You must have permissions to delete messages in the channel to do this")
            return
        if ctx.channel.permissions_for(user).administrator and user != self.bot.user:
            raise BadArgument("The messages of an administrator can not be deleted")
        if time_period > 31 * 24 * 60 * 60:
            await ctx.send("Maximum purge user length is 31 days")
            return

        message = ctx.author.mention + ": {} all messages sent by " + user.mention + " in the last " + humanfriendly.format_timespan(time_period) + "{}"
        await self._do_purge(ctx, time_period, message, lambda x: x.author == user)

    async def _do_purge(self, ctx, time_period, message, check=None):
        if await self.confirm(ctx, message.format("Are you sure you want to purge", "?")):
            in_progress = await ctx.send(message.format("Purging", "!"))
            start_time = datetime.datetime.now() - datetime.timedelta(seconds=time_period)

            with ctx.channel.typing():
                await ctx.channel.purge(limit=None, after=start_time, check=check)

            await safe_delete(in_progress)
            await ctx.send(message.format("Successfully purged", "."))
        else:
            await ctx.send(message.format("Cancelled purge of", "."))
