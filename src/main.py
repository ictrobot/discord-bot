import asyncio

import discord
from discord.ext import commands
from bot.setup_logging import logger
from bot.events import EventRegistry
from bot.modules import module_list
from bot.module import Module
from peewee import SqliteDatabase

# https://github.com/Rapptz/discord.py/blob/rewrite/examples/basic_bot.py
DESCRIPTION = '''Useful utilities\n\nSource: https://github.com/ictrobot/discord-bot/'''


class Instance:

    def __init__(self):
        self.logger = logger
        self.modules = {}
        self.discord_bot = commands.Bot(command_prefix='!', description=DESCRIPTION, game=discord.Game(name="Server Management"))
        self.event_registry = EventRegistry(self)
        self.db = SqliteDatabase("../bot.db", pragmas=[('foreign_keys', 'on')])
        self.load_modules()
        self.setup_db()

    def setup_db(self):
        models = []
        for module in self.modules.values():
            if module.db_models:
                models += module.db_models
        self.logger.debug("Trying to connect to DB")
        self.db.connect()
        self.logger.info("DB Tables: " + ", ".join(x.__name__ for x in models))
        self.db.create_tables(models)
        self.logger.info("Successfully connected to DB")

    def load_modules(self):
        found_modules = []
        for module in module_list:
            found = False
            for name, value in module.__dict__.copy().items():
                if isinstance(value, type) and issubclass(value, Module) and value != Module:
                    found_modules.append(value)
                    found = True
            if not found:
                self.logger.warn("Module {} does not declare any bot modules".format(module))
        for module in found_modules:
            self.logger.info("Initializing module {}".format(module.__name__))
            try:
                self.modules[module] = module(self)
            except Exception as e:
                self.logger.exception("Error initializing module {}".format(module.__name__))

    def run(self):
        with open("../token.txt", "r") as tokenFile:
            self.discord_bot.run(tokenFile.read().strip(), bot=True)

    def schedule(self, f):
        self.discord_bot.loop.call_soon(asyncio.ensure_future, f)


if __name__ == "__main__":
    Instance().run()
