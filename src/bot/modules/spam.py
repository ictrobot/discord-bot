import datetime
from io import BytesIO
import hashlib

import imagehash
from PIL import Image
from peewee import *

from bot.module import *


class AttachmentHash(Model):
    message_id = IntegerField()
    hash = TextField()
    datetime = TimestampField()

    class Meta:
        database = Proxy()


class SpamWarning(Model):
    user_id = IntegerField()
    channel_id = IntegerField()
    datetime = TimestampField()

    class Meta:
        primary_key = CompositeKey('user_id', 'channel_id')
        database = Proxy()


class SpamModule(Module):

    def __init__(self, instance):
        super().__init__(instance, "spam", db_models=[AttachmentHash, SpamWarning])

    async def ratelimit(self, message):
        if message.author == self.bot.user or (message.channel.permissions_for(message.author).administrator and "!hash" not in message.content):
            return
        appearances = 0
        warning_present = False
        warning_msg = "Please don't spam {}".format(message.author.mention)
        check_start = datetime.datetime.now() - datetime.timedelta(days=1)
        if message.attachments:
            attachments = []
            for attachment in message.attachments:
                f = BytesIO()
                await attachment.save(f)

                if attachment.width:
                    img = Image.open(f)
                    attachment_hash = imagehash.dhash(img)
                    hash_type = "Image Hash"
                else:
                    m = hashlib.sha256()
                    m.update(f.getbuffer())
                    attachment_hash = m.hexdigest()
                    hash_type = "SHA256"

                attachments.append(attachment_hash)
                AttachmentHash(message_id=message.id, datetime=message.created_at, hash=attachment_hash).save(force_insert=True)
                print(attachment.url, attachment_hash)
                f.close()

                if "!hash" in message.content:
                    await message.channel.send("{} of {}\n{}".format(hash_type, attachment.url, attachment_hash))
            if message.channel.permissions_for(message.author).administrator:
                return

            filter = AttachmentHash.hash == attachments[0]
            for img_hash in attachments[1:]:
                filter |= img_hash

            discord_ids = []
            for entry in AttachmentHash.select().where(filter):
                if entry.datetime > check_start:
                    discord_ids.append(entry.message_id)

            async for previous_message in message.channel.history(limit=50):
                if previous_message.author == message.author and previous_message.id in discord_ids:
                    appearances += 1
                if previous_message.content == warning_msg:
                    warning_present = True
        else:
            async for previous_message in message.channel.history(limit=25):
                if previous_message.created_at < check_start:
                    break
                if previous_message.author == message.author and previous_message.content == message.content:
                    appearances += 1
                if previous_message.content == warning_msg:
                    warning_present = True

        if appearances >= 4:
            await safe_delete(message)
            if not warning_present:
                spam_warning, just_created = SpamWarning.get_or_create(user_id=message.author.id, channel_id=message.channel.id, defaults={"datetime": message.created_at})
                if just_created:
                    await message.channel.send(warning_msg)
                elif spam_warning.datetime + datetime.timedelta(hours=2) < message.created_at:
                    spam_warning.datetime = message.created_at
                    spam_warning.save()
                    await message.channel.send(warning_msg)
            return True

    @add_event_handler(1100)
    async def on_message(self, message):
        if await self.ratelimit(message):
            return True
