import glob
import importlib
from os.path import dirname, basename, isfile


module_names = [basename(f)[:-3] for f in glob.glob(dirname(__file__) + "/*.py") if isfile(f) and not f.endswith('__init__.py')]
module_list = [importlib.import_module("bot.modules." + m) for m in module_names]

del glob, importlib, dirname, basename, isfile
