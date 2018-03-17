from bot.module import *
import discord


TMP_CHANNEL_NAME = "tmp-msg"
TMP_TIME = 60


class TempCommand(Module):

    def __init__(self, instance):
        super().__init__(instance, "temp_command")

    @add_command(brief="Deletes message after a short time period", aliases=["tmp"], ignore_extra=True)
    async def temp(self, ctx):
        await ctx.message.add_reaction("🕑")
        await asyncio.sleep(TMP_TIME - 5)
        for symbol in ["5⃣", "4⃣", "3⃣", "2⃣", "1⃣"]:
            await ctx.message.add_reaction(symbol)
            await asyncio.sleep(1)
            await ctx.message.remove_reaction(symbol, self.bot.user)
        await safe_delete(ctx.message)


class TempChannel(Module):

    def __init__(self, instance):
        super().__init__(instance, "temp_channel")

    @add_event_handler(900)
    async def on_message(self, message):
        if isinstance(message.channel, discord.TextChannel) and message.channel.name == TMP_CHANNEL_NAME:
            await asyncio.sleep(TMP_TIME)
            await safe_delete(message)
            return True

    @add_event_handler(1)
    async def on_ready(self):
        for channel in self.bot.get_all_channels():
            if channel.name == TMP_CHANNEL_NAME:
                async for message in channel.history(limit=1000):
                    self.instance.schedule(self.on_message(message))
                    await asyncio.sleep(0.01)
