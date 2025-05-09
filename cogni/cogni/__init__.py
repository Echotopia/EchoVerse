"""Cogni framework initialization."""



import os

if int(os.getenv('COGNI_DEBUG', "0")) ==1:
    import backtrace

    backtrace.hook(
        reverse=False,
        align=False,
        strip_path=False,
        enable_on_envvar_only=False,
        on_tty=False,
        conservative=False,
        styles={}
        )

import traceback
from functools import wraps

def log_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (Exception, NameError, AttributeError):
            log_dir = "./elogs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{func.__name__}_error.log")
            with open(log_file, "a") as f:
                f.write(f"Exception in {func.__name__}:\n")
                f.write(traceback.format_exc())
                f.write("\n")
            raise  # Re-raise to maintain original behavior
    return wrapper


from functools import wraps
import os
from .entities import Message, Conversation
from .wrappers import tool as _tool, Tool, MW, mw, Agent, State, Event, ES, on, Stream
tool = lambda f, name=None: _tool(log_exceptions(f), name)

from .magicimport import dynamic_import
from .utils import use_tools
import yaml

from rich import print

import os
absolutize = lambda path: os.getcwd() +'/' + path

def load_yaml(file_path=absolutize('./CONF.yaml')):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

if not "stuff" in State:
    State["stuff"] = {}
    



# usage example:
State['CONF'] = load_yaml()
CONF = State['CONF']
State['stuff']['cwd'] = os.getcwd()
State['stuff']['DRAWIO_DIR'] = absolutize(CONF.DRAWIO_DIR)
State['stuff']['CODE_DIR'] = absolutize(CONF.CODE_DIR)
State['stuff']['IMAGE_DIR'] = absolutize(CONF.IMAGE_DIR)
for dir_name in [
    'tools',
    'agents',
    'middlewares',
]:
    dynamic_import(dir_name)
    

__all__ = [
    'Message',
    'Conversation',
    'tool',
    'Tool',
    'mw',
    'MW',
    'Agent',
    'drawio_agent',
    'State',
    'Event',
    'ES',
    'use_tools',
    'log_exceptions',
]
