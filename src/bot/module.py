import logging
import asyncio
import discord
import inspect


def add_command(*add_args, **add_kwargs):
    def wrapper(f):
        f.add_command = True
        f.ac_args = add_args
        f.ac_kwargs = add_kwargs
        return f
    return wrapper


def add_event_handler(priority, eventname=None):
    def wrapper(f):
        f.add_event_handler = True
        f.ae_priority = priority
        f.ae_eventname = eventname
        return f
    return wrapper


def channel_name(channel):
    if isinstance(channel, discord.TextChannel) or isinstance(channel, discord.VoiceChannel) or isinstance(channel, discord.CategoryChannel):
        return channel.guild.name + "#" + channel.name
    elif isinstance(channel, discord.DMChannel):
        return "@" + channel.recipient.name
    elif isinstance(channel, discord.GroupChannel):
        return channel.name if channel.name else ",".join("@" + x.user.name for x in channel.recipients)


class Module:
    def __init__(self, instance, group_name):
        self.instance = instance
        self.bot = instance.discord_bot
        self.logger = logging.Logger("bot." + group_name)
        self.register()

    def register(self):
        for name, method in inspect.getmembers(self, inspect.ismethod):
            f = method.__func__

            try:
                if f.add_command:
                    self.name = self.bot.command(*f.ac_args, **f.ac_kwargs)(method)
            except AttributeError:
                pass

            try:
                if f.add_event_handler:
                    self.instance.event_registry.add_handler(method, f.ae_priority, event_name=f.ae_eventname)
            except AttributeError:
                pass

    async def confirm(self, ctx, text):
        warning_msg = await ctx.send(text)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in '☑🚫'

        await warning_msg.add_reaction('🚫')
        await warning_msg.add_reaction('☑')

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
        except asyncio.TimeoutError:
            await warning_msg.delete()
            return False
        else:
            await warning_msg.delete()
            return str(reaction.emoji) == "☑"
