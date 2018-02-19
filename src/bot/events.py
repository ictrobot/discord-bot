from discord.ext.commands.errors import BadArgument, MissingRequiredArgument, CommandNotFound
import asyncio


class EventRegistry:

    def __init__(self, instance):
        self.instance = instance

        self.add_handler(self._on_message_process_commands, 1000, event_name="on_message")
        self.add_handler(self._on_ready_log, 1000, event_name="on_ready")
        self.add_handler(self._on_command_error, 1000, event_name="on_command_error")

    def add_handler(self, handler, priority, event_name=None):
        if not event_name:
            event_name = handler.__name__

        if not hasattr(self, event_name):
            setattr(self, event_name, [])

            async def super_handler(*args, **kwargs):
                for h, p in getattr(self, event_name):
                    try:
                        if await h(*args, **kwargs):
                            return
                    except Exception as e:
                        self.instance.logger.exception("Error running event {} on handler {}".format(event_name, handler.__name__))

            super_handler.__name__ = event_name
            self.instance.discord_bot.event(super_handler)

        handler_list = getattr(self, event_name)
        handler_list.append((handler, priority))
        handler_list.sort(key=lambda x: x[1], reverse=True)

    # Default event handlers
    async def _on_message_process_commands(self, message):
        await self.instance.discord_bot.process_commands(message)

    async def _on_ready_log(self):
        self.instance.logger.info('Successfully logged in. Name: "{0.name}". ID: {0.id}'.format(self.instance.discord_bot.user))

    async def _on_command_error(self, ctx, error):
        to_delete = []
        raise_error = False
        if isinstance(error, BadArgument) or isinstance(error, MissingRequiredArgument):
            command = next(filter(lambda x: x.name == ctx.invoked_with, ctx.bot.commands))

            to_delete.append(await ctx.send("**Error:** *{}*\n*This message will delete automatically*".format(error.args[0])))
            for page in await ctx.bot.formatter.format_help_for(ctx, command):
                to_delete.append(await ctx.send(page))
        elif isinstance(error, CommandNotFound):
            self.instance.logger.debug(error.args[0])
        else:
            to_delete.append(await ctx.send("Unknown error occurred when processing command *{}*.\n*This message will delete automatically*".format(ctx.invoked_with)))
            raise_error = True

        try:
            if to_delete:
                await asyncio.sleep(15)
                await ctx.channel.delete_messages(to_delete)
        except Exception as e:
            pass
        if raise_error:
            raise Exception("Command {} raised an exception".format(ctx.invoked_with)) from error
