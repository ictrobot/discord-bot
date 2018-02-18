import logging.handlers
import sys
import os

LOG_FORMATTER = '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'

if not os.path.exists("../logs/"):
    os.makedirs("../logs/")

file_debug_handler = logging.handlers.RotatingFileHandler(filename='../logs/bot-debug.log', encoding='utf-8', mode='w', maxBytes=1024 * 1024, backupCount=5)
file_debug_handler.setLevel(logging.DEBUG)
file_debug_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
logging.root.addHandler(file_debug_handler)

file_info_handler = logging.handlers.RotatingFileHandler(filename='../logs/bot-info.log', encoding='utf-8', mode='w', maxBytes=1024 * 1024, backupCount=5)
file_info_handler.setLevel(logging.INFO)
file_info_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
logging.root.addHandler(file_info_handler)

file_error_handler = logging.handlers.RotatingFileHandler(filename='../logs/bot-error.log', encoding='utf-8', mode='w', maxBytes=1024 * 1024, backupCount=5)
file_error_handler.setLevel(logging.ERROR)
file_error_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
logging.root.addHandler(file_error_handler)


class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO)


console_info_handler = logging.StreamHandler(sys.stdout)
console_info_handler.setLevel(logging.INFO)
console_info_handler.addFilter(InfoFilter())
console_info_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
logging.root.addHandler(console_info_handler)

console_error_handler = logging.StreamHandler(sys.stderr)
console_error_handler.setLevel(logging.WARNING)
console_error_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
logging.root.addHandler(console_error_handler)

discordLogger = logging.getLogger('discord')
discordLogger.setLevel(logging.DEBUG)

logger = logging.getLogger("bot")
logger.setLevel(logging.DEBUG)
