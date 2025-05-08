import time
import threading
from cogni import tool

_lock = threading.Lock()

@tool
def _ensure_exec_state():
    """Ensure the 'exec' namespace exists in State."""
    from cogni import State
    if 'exec' not in State:
        State['exec'] = {
            'tree': {},
            'logs': [],
            'pause_before': None,
            'waiting': False,
            'resume': False
        }

@tool
def step():
    """Advance execution by setting resume flag."""
    from cogni import State
    _ensure_exec_state()
    with _lock:
        State['exec']['resume'] = True

@tool
def exec_agent_start(agent_name: str):
    """Record start of agent execution and push to tree."""
    from cogni import State
    _ensure_exec_state()
    if not isinstance(State['exec'].to_dict().get('tree'), dict):
        State['exec']['tree'] = {}
    timestamp = time.time()
    with _lock:
        State['exec']['tree'][timestamp] = agent_name
        State['exec']['pause_before'] = 'agent'

@tool
def exec_agent_end(agent_name: str):
    """Record end of agent execution and pop from tree."""
    from cogni import State
    _ensure_exec_state()
    with _lock:
        for ts, name in list(State['exec']['tree'].items()):
            if name == agent_name:
                del State['exec']['tree'][ts]
        State['exec']['pause_before'] = None

@tool
def exec_tool_start(tool_name: str, args):
    """Record start of a tool invocation."""
    from cogni import State
    _ensure_exec_state()
    if not isinstance(State['exec']['logs'], list):
        State['exec']['logs'] = []
    entry = {
        'tool': tool_name,
        'args': args,
        'start': time.time()
    }
    with _lock:
        State['exec']['logs'].append(entry)
        State['exec']['pause_before'] = 'tool'

@tool
def exec_tool_end(tool_name: str, result):
    """Record end of a tool invocation and its result."""
    from cogni import State
    _ensure_exec_state()
    end_time = time.time()
    with _lock:
        for entry in reversed(State['exec']['logs']):
            if entry.get('tool') == tool_name and 'end' not in entry:
                entry['result'] = result
                entry['end'] = end_time
                break
        State['exec']['pause_before'] = None
