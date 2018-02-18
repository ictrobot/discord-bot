from bot.module import *


class SpamModule(Module):

    def __init__(self, instance):
        super().__init__(instance, "spam")

    async def ratelimit(self, message):
        if message.author == self.bot.user or message.channel.permissions_for(message.author).administrator:
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

    @add_event_handler(1001)
    async def on_message(self, message):
        if await self.ratelimit(message):
            return True
