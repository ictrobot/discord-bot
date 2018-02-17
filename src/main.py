import asyncio
import datetime

import discord
import humanfriendly
from discord.ext import commands

NUMBERS = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣"]
TIME_PERIODS = {"m": 60, "minute": 60, "minutes": 60, "h": 3600, "hour": 3600, "hours": 3600, "d": 86400, "day": 86400, "days": 86400}

TMP_CHANNEL_NAME = "tmp-msg"
TMP_CHANNEL_TIME = 60

# https://github.com/Rapptz/discord.py/blob/rewrite/examples/basic_bot.py
description = '''General usual bot\n\nSource: https://github.com/ictrobot/discord-bot/'''
bot = commands.Bot(command_prefix='!', description=description, game=discord.Game(name="Server Management"))

POLLS = []

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


@bot.command(brief="Purges messages from one user", description="Purges messages. Examples: '!purgeuser @user 1 hour', '!purgeuser @user 2 days'")
async def purgeuser(ctx, user: discord.Member, num: int, timeString: str):
    if not ctx.channel.permissions_for(ctx.author).administrator:
        await ctx.send("You must be an administrator to do this")
        return
    if ctx.channel.permissions_for(user).administrator and user != bot.user:
        await ctx.send("The messages of an administrator can not be deleted")
        return
    if timeString not in TIME_PERIODS:
        await ctx.send("{} isn't a valid time period".format(timeString))
        return
    seconds = num * TIME_PERIODS[timeString]
    if seconds > 31 * 24 * 60 * 60:
        await ctx.send("Maximum purge user length is 31 days")
        return
    if ctx.channel.name == TMP_CHANNEL_NAME:
        await ctx.send("That doesn't make sense here...")
        return
    confirm_message = "{}: Are you sure you want to purge messages sent by {} in the last {}?".format(ctx.author.mention, user.mention, humanfriendly.format_timespan(seconds))
    if await confirm(ctx, confirm_message):
        await ctx.send("Purging")
        start_time = datetime.datetime.now() - datetime.timedelta(seconds=seconds)

        def check_message(message):
            return message.author == user

        await ctx.channel.purge(limit=10000, after=start_time, check=check_message)

        await ctx.send("{}: successfully purged all messages sent by {} in the last {}".format(ctx.author.mention, user.mention, humanfriendly.format_timespan(seconds)))
    else:
        await ctx.send("Cancelled purge of {}'s messages".format(user.mention))


@bot.command(brief="Deletes message after a short time period", aliases=["tmp"])
async def temp(ctx, *message):
    await ctx.message.add_reaction("🕑")
    await asyncio.sleep(TMP_CHANNEL_TIME - 5)
    for symbol in ["5⃣", "4⃣", "3⃣", "2⃣", "1⃣"]:
        await ctx.message.add_reaction(symbol)
        await asyncio.sleep(1)
        await ctx.message.remove_reaction(symbol, bot.user)
    await ctx.message.delete()


@bot.command(brief="Run a poll")
async def poll(ctx, title, *options):
    if len(options) < 2:
        await ctx.send("There must be at least 2 options")
        return
    if len(options) > 9:
        await ctx.send("There must be less than 10 options")
        return
    message = await ctx.send("Poll from {}:\n`{}`\n\n".format(ctx.author.mention, title) + "\n".join("{} - `{}`".format(n, o) for n, o in zip(NUMBERS, options)) + "\n\n*To vote click the corresponding number reaction. {} can click ⛔ to end the poll*".format(ctx.author.mention))
    await message.add_reaction("📄")
    for n in NUMBERS[:len(options)]:
        await message.add_reaction(n)
    await message.add_reaction("📝")
    await message.add_reaction("⛔")
    POLLS.insert(0, {"user": ctx.author.id, "channel": ctx.message.channel.id, "message": message.id, "title": title, "options": options})


@bot.event
async def on_reaction_add(reaction, user):
    if user and str(reaction) == "⛔" and reaction.message.author == bot.user and reaction.message.content.startswith("Poll from "):
        poll = None
        for check in POLLS:
            if check["channel"] == reaction.message.channel.id and check["message"] == reaction.message.id:
                poll = check
                break
        if poll and poll["user"] == user.id:
            POLLS.remove(poll)
            await endpoll(poll, reaction.message)


async def endpoll(poll, message):
    response = "Results from {}'s poll:\n`{}`\n\n".format(message.channel.guild.get_member(poll["user"]).mention, poll["title"])

    results = []
    for i, (n, o) in enumerate(zip(NUMBERS, poll["options"])):
        for r in message.reactions:
            if str(r) == n:
                users = []
                async for user in r.users():
                    if user != bot.user:
                        users.append(user)
                results.append((i, n, o, users))
                break
    results.sort(key=lambda x: (-len(x[3]), x[0]))

    for i, n, o, users in results:
        response += "{} - `{}`\n".format(n, o)
        if len(users) == 0:
            response += "No votes\n"
        else:
            response += "{} votes:\n".format(len(users))
        for user in users:
            response += "- {}\n".format(user.mention)
    await message.channel.send(response)
    await message.delete()


with open("../token.txt", "r") as tokenFile:
    bot.run(tokenFile.read().strip(), bot=True)
