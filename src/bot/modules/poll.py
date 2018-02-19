from bot.module import *
from collections import defaultdict
from peewee import *
import humanfriendly

NUMBERS = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣"]


class Poll(Model):
    message_id = IntegerField(primary_key=True)
    user_id = IntegerField()
    text = TextField()
    multiple_answers = BooleanField()

    class Meta:
        database = Proxy()


class PollOption(Model):
    poll = ForeignKeyField(Poll, backref="options", on_delete="CASCADE")
    num = IntegerField()
    text = TextField()

    class Meta:
        primary_key = CompositeKey("poll", "num")
        database = Proxy()


class PollCommand(Module):

    def __init__(self, instance):
        super().__init__(instance, "poll", db_models=[Poll, PollOption])

    @add_command(brief="Run a poll")
    async def poll(self, ctx, title, *options):
        await self.do_poll(ctx, title, options, False)

    @add_command(brief="Run a poll where people can vote for multiple answers")
    async def pollmultiple(self, ctx, title, *options):
        await self.do_poll(ctx, title, options, True)

    async def do_poll(self, ctx, title, options, multiple_answers):
        if len(options) < 2:
            await ctx.send("There must be at least 2 options")
            return
        if len(options) > 9:
            await ctx.send("There must be less than 10 options")
            return

        message_text = "Poll from {}:\n`{}`\n\n".format(ctx.author.mention, title)
        message_text += "\n".join("{} - `{}`".format(n, o) for n, o in zip(NUMBERS, options))
        message_text += "\n\n*To vote click the corresponding number reaction.* "
        if multiple_answers:
            message_text += "**You may vote for multiple choices.** "
        else:
            message_text += "**Only vote for one choice or your votes will not be counted.** "
        message_text += "*{} can click ⛔ to end the poll*".format(ctx.author.mention)

        message = await ctx.send(message_text)
        await message.add_reaction("📄")
        for n in NUMBERS[:len(options)]:
            await message.add_reaction(n)
        await message.add_reaction("📝")
        await message.add_reaction("⛔")

        with self.instance.db.atomic() as transaction:
            poll = Poll(message_id=message.id, user_id=ctx.author.id, text=title, multiple_answers=multiple_answers)
            poll.save(force_insert=True)
            for i, option in enumerate(options):
                PollOption(poll=poll, num=i, text=option).save(force_insert=True)

    @add_event_handler(1)
    async def on_raw_reaction_add(self, emoji, message_id, channel_id, user_id):
        if str(emoji) == "⛔" and user_id != self.bot.user.id:
            channel = self.bot.get_channel(channel_id)
            message = await channel.get_message(message_id)
            if message.author == self.bot.user and message.content.startswith("Poll from "):
                try:
                    poll = Poll.get(Poll.message_id == message.id)
                except DoesNotExist:
                    return
                if poll.user_id == user_id:
                    options = [opt.text for opt in PollOption.select().where(PollOption.poll == poll).order_by(PollOption.num)]
                    await self.endpoll(poll, self.bot.get_user(user_id), options, message)
                    with self.instance.db.atomic() as transaction:
                        Poll.delete().where(Poll.message_id == message_id).execute()
                    return True

    async def endpoll(self, poll, user, options, message):
        response = "Results from {}'s poll:\n`{}`\n\n".format(user.mention, poll.text)

        results = []
        for i, (n, o) in enumerate(zip(NUMBERS, options)):
            for r in message.reactions:
                if str(r) == n:
                    users = []
                    async for user in r.users():
                        if user != self.bot.user:
                            users.append(user)
                    results.append((i, n, o, users))
                    break

        not_counted = []
        if not poll.multiple_answers:
            user_vote_count = defaultdict(int)
            for r in results:
                for u in r[3]:
                    user_vote_count[u] += 1

            for u, count in user_vote_count.items():
                if count > 1:
                    not_counted.append(u)

            for u in not_counted:
                for r in results:
                    if u in r[3]:
                        r[3].remove(u)

        results.sort(key=lambda x: (-len(x[3]), x[0]))

        for i, n, o, users in results:
            response += "{} - `{}`\n".format(n, o)
            if len(users) == 0:
                response += "No votes\n"
            else:
                response += "{}:\n".format(humanfriendly.pluralize(len(users), "vote"))
            for user in users:
                response += "- {}\n".format(user.mention)

        if len(not_counted) > 0:
            response += "\n\nVotes from {} were not counted as they voted more than once".format(", ".join(u.mention for u in not_counted))

        await message.channel.send(response)
        await message.delete()
