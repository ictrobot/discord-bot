import asyncio
import datetime

import discord
import humanfriendly
from discord.ext import commands

TIME_PERIODS = {"m": 60, "minute": 60, "minutes": 60, "h": 3600, "hour": 3600, "hours": 3600, "d": 86400, "day": 86400, "days": 86400}

TMP_CHANNEL_NAME = "tmp-msg"
TMP_CHANNEL_TIME = 60

# https://github.com/Rapptz/discord.py/blob/rewrite/examples/basic_bot.py
description = '''General usual bot\n\nSource: https://github.com/ictrobot/discord-bot/'''
bot = commands.Bot(command_prefix='!', description=description, game=discord.Game(name="Server Management"))


@bot.event
async def on_ready():
    print('Successfully logged in. Name: "{}". ID: {}'.format(bot.user.name, bot.user.id))
    for channel in bot.get_all_channels():
        if channel.name == TMP_CHANNEL_NAME:
            async for message in channel.history(limit=1000):
                bot.loop.call_soon(asyncio.ensure_future, on_message(message))
                await asyncio.sleep(0.01)


async def ratelimit(message):
    if message.author == bot.user or message.channel.permissions_for(message.author).administrator:
        return
    appearances = 0
    warning_present = False
    warning_msg = "Please don't spam {}".format(message.author.mention)
    async for previous_message in message.channel.history(limit=25):
        if previous_message.content == message.content and previous_message.author == message.author:
            appearances += 1
        if previous_message.content == warning_msg:
            warning_present = True
    if appearances >= 4:
        await message.delete()
        if not warning_present:
            await message.channel.send(warning_msg)
        return True


@bot.event
async def on_message(message):
    if await ratelimit(message):
        return
    await bot.process_commands(message)
    if message.channel.name == TMP_CHANNEL_NAME:
        await asyncio.sleep(TMP_CHANNEL_TIME)
        if not message.pinned:
            await message.delete()
            return


async def confirm(ctx, text):
    warning_msg = await ctx.send(text)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in '☑🚫'

    await warning_msg.add_reaction('🚫')
    await warning_msg.add_reaction('☑')

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=120, check=check)
    except asyncio.TimeoutError:
        await warning_msg.delete()
        return False
    else:
        await warning_msg.delete()
        return str(reaction.emoji) == "☑"


@bot.command(brief="Purges messages", description="Purges messages. Examples: '!purge 1 hour', '!purge 2 days'")
async def purge(ctx, num: int, timeString: str):
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send("You must be an administrator to do this")
        return
    if timeString not in TIME_PERIODS:
        await ctx.send("{} isn't a valid time period".format(timeString))
        return
    seconds = num * TIME_PERIODS[timeString]
    if seconds > 3 * 24 * 60 * 60:
        await ctx.send("Maximum purge length is 3 days")
        return
    if ctx.channel.name == TMP_CHANNEL_NAME:
        await ctx.send("That doesn't make sense here...")
        return
    confirm_message = "{}: Are you sure you want to purge messages sent in the last {}?".format(ctx.author.mention, humanfriendly.format_timespan(seconds))
    if await confirm(ctx, confirm_message):
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


@bot.command(brief="Deletes message after a short time period", aliases=["tmp"])
async def temp(ctx, *message):
    await ctx.message.add_reaction("🕑")
    await asyncio.sleep(TMP_CHANNEL_TIME - 5)
    for symbol in ["5⃣", "4⃣", "3⃣", "2⃣", "1⃣"]:
        await ctx.message.add_reaction(symbol)
        await asyncio.sleep(1)
        await ctx.message.remove_reaction(symbol, bot.user)
    await ctx.message.delete()

with open("../token.txt", "r") as tokenFile:
    bot.run(tokenFile.read().strip(), bot=True)
