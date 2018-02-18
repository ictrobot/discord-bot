class EventRegistry:

    def __init__(self, instance):
        self.instance = instance

        self.add_handler(self._on_message_process_commands, 1000, event_name="on_message")
        self.add_handler(self._on_ready_log, 1000, event_name="on_ready")

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
