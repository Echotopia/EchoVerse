# func_wrapper.py

import os
import traceback
from typing import Any, Callable
from .instances_store import InstancesStore


class FuncWrapper(metaclass=InstancesStore):
    """
    Base wrapper class for functions providing registration, access, and enhanced
    exception logging.

    Exceptions thrown during execution of wrapped functions are caught, logged,
    and re-raised. Logs are stored in sequential markdown files under ./tool_logs/.
    """

    @classmethod
    def register(cls, func: Callable, name: str = None) -> 'FuncWrapper':
        """Register a function, storing it by name for global access."""
        if not hasattr(func, '__name__'):
            setattr(func, '__name__', name)
        name = name or func.__name__

        instance = cls(name, func)
        cls[name] = instance
        return instance

    def __init__(self, name: str, func: Callable):
        self.name = name
        self._func = func

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the wrapped function, logging uncaught exceptions."""
        try:
            return self._func(*args, **kwargs)
        except Exception as e:
            self._log_exception(e)
            raise  # Re-raise the original exception after logging

    def _log_exception(self, exception: Exception):
        """Log the exception details, filtering frames to include only project files."""
        tb = traceback.extract_tb(exception.__traceback__)
        project_root = os.getcwd()
        filtered_frames = [
            frame for frame in tb
            if os.path.commonpath([project_root, os.path.abspath(frame.filename)]) == project_root
        ]

        if not filtered_frames:
            # No relevant frames to log; skip logging
            return

        # Prepare log directory
        log_dir = "tool_logs"
        os.makedirs(log_dir, exist_ok=True)

        # Find the next available log file number
        log_index = 0
        while os.path.exists(os.path.join(log_dir, f"{log_index}.md")):
            log_index += 1

        # Write the exception log
        log_path = os.path.join(log_dir, f"{log_index}.md")
        with open(log_path, "w") as log_file:
            # Write exception type as a header
            log_file.write(f"# {type(exception).__name__}\n")
            # Write exception message
            log_file.write(f"{exception}\n\n")

            log_file.write("# Stack\n")

            # Write each filtered frame
            for frame in filtered_frames:
                relative_path = os.path.relpath(frame.filename, project_root)
                log_file.write(f"- [../{relative_path}](../{relative_path}#L{frame.lineno})\n")

    def __repr__(self) -> str:
        """String representation of the wrapped function."""
        return f"{self.__class__.__name__}['{self.name}']"
