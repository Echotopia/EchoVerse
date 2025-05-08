import time
from cogni import mw, State

@mw
def exec_pause(ctx, conv):
    """Pause before agent or tool execution based on State['exec']['pause_before']."""
    mode = State['exec'].get('pause_before')
    if mode and not State['exec'].get('resume'):
        State['exec']['waiting'] = True
        while not State['exec'].get('resume'):
            time.sleep(0.05)
        State['exec']['waiting'] = False
        State['exec']['resume'] = False
    return conv
