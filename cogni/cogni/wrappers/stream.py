from time import time

class _Stream:
    def __init__(self):
        from .state import State
        self.last_stream_event = -1
        State['stream_buffer']['current_stream'] = ""
        
        
    @property
    def stream(self):
        from .state import State
        State.reset_cache()
        
        return State['stream_buffer']['current_stream']
    
    @stream.setter
    def stream(self, value):
        from .state import State
        
        State['stream_buffer']['current_stream'] = value
        
Stream = _Stream()