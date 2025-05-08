from cogni import tool, State

import random

def rand_hex(): return ''.join(random.choice('0123456789abcdef') for _ in range(9))



@tool
def cocode(content):
    if not "cocoding" in State:
        State['cocoding'] = {"tasks":{}}
        
    State['cocoding']['tasks'][rand_hex()] = content
    
    return "task added :)"