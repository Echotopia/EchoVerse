import os
import json
import shutil
import re
from typing import Any, Dict, List, Union


def safe_path_component(component: str) -> str:
    """Convert a string to a safe path component by replacing unsafe characters."""
    # Replace characters that might be problematic in file paths
    safe = re.sub(r'[\\/*?:"<>|]', '_', component)
    return safe


class StateDict:
    """A wrapper for dictionaries that provides attribute-style access and automatic persistence"""

    def __init__(self, data: Dict = None, parent: '_State' = None, state_name: str = None, path: List[str] = None):
        self._data = {}
        self._parent = parent
        self._state_name = state_name
        self._path = path or []
        
        # Create this directory first
        if self._parent and self._state_name:
            dir_path = self._get_dir_path()
            os.makedirs(dir_path, exist_ok=True)
            
            # Write type file
            type_file = os.path.join(dir_path, '__type.json')
            with open(type_file, 'w') as f:
                json.dump({"type": "dict"}, f)
        
        # Then process data
        if data:
            for k, v in data.items():
                if isinstance(v, dict):
                    self._data[k] = StateDict(v, parent, state_name, self._path + [k])
                elif isinstance(v, list):
                    self._data[k] = StateList(v, parent, state_name, self._path + [k])
                else:
                    self._data[k] = v
                    # Persist scalar values immediately
                    if self._parent and self._state_name:
                        key_dir = os.path.join(self._get_dir_path(), safe_path_component(k))
                        os.makedirs(key_dir, exist_ok=True)
                        val_file = os.path.join(key_dir, 'val.json')
                        with open(val_file, 'w') as f:
                            json.dump(v, f)

    def __len__(self):
        return len(self._data)

    def _persist(self):
        """Save this StateDict to the file system."""
        if not (self._parent and self._state_name):
            return
            
        # Get the directory path for this StateDict
        dir_path = self._get_dir_path()
        
        # Create the directory if it doesn't exist
        os.makedirs(dir_path, exist_ok=True)
        
        # Write the type file indicating this is a dictionary
        type_file_path = os.path.join(dir_path, '__type.json')
        with open(type_file_path, 'w') as f:
            json.dump({"type": "dict"}, f)
        
        # Persist each value (nested objects will persist themselves)
        for k, v in self._data.items():
            # Check if it's a container that will persist itself
            if isinstance(v, (StateDict, StateList)):
                continue
                
            # For scalar values, create a directory and value file
            key_dir = os.path.join(dir_path, safe_path_component(k))
            os.makedirs(key_dir, exist_ok=True)
            
            val_file = os.path.join(key_dir, 'val.json')
            with open(val_file, 'w') as f:
                json.dump(v, f)

    def _get_dir_path(self) -> str:
        """Get the directory path for this StateDict."""
        if not self._parent or not self._state_name:
            return None
        
        # Start with the states directory
        dir_path = self._parent._states_dir
        
        # Build path from state name and additional path components
        components = [self._state_name] + self._path
        for component in components:
            dir_path = os.path.join(dir_path, safe_path_component(str(component)))
        
        return dir_path
    def setdefault(self, key, value):
        if not key in self:
            self[key] = value
        return self[key]
            
            
    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'StateDict' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith('_'):
            super().__setattr__(name, value)
            return
        
        # If we're setting a dict on an existing StateDict, merge them instead of replacing
        if isinstance(value, dict) and name in self._data and isinstance(self._data[name], StateDict):
            # Get the existing StateDict
            existing_dict = self._data[name]
            
            # Update it with new values
            for k, v in value.items():
                existing_dict[k] = v
        else:
            # Standard behavior for non-dictionary values or new keys
            if isinstance(value, dict):
                self._data[name] = StateDict(value, self._parent, self._state_name, self._path + [name])
            elif isinstance(value, list):
                self._data[name] = StateList(value, self._parent, self._state_name, self._path + [name])
            else:
                # For scalar values, update the value in memory
                self._data[name] = value
                
                # Update the value file
                if self._parent and self._state_name:
                    key_dir = os.path.join(self._get_dir_path(), safe_path_component(name))
                    os.makedirs(key_dir, exist_ok=True)
                    val_file = os.path.join(key_dir, 'val.json')
                    with open(val_file, 'w') as f:
                        json.dump(value, f)
        
        # Notify parent of changes
        if self._parent and self._state_name:
            self._parent._notify_change(self._state_name)

    def __getitem__(self, key: str) -> Any:
        if key not in self._data:
            self._data[key] = StateDict({}, self._parent, self._state_name, self._path + [key])
            # The new StateDict will persist itself
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        # If we're setting a dict on an existing StateDict, merge them instead of replacing
        if isinstance(value, dict) and key in self._data and isinstance(self._data[key], StateDict):
            # Get the existing StateDict
            existing_dict = self._data[key]
            
            # Update it with new values
            for k, v in value.items():
                existing_dict[k] = v
        else:
            # Standard behavior for non-dictionary values or new keys
            if isinstance(value, dict):
                self._data[key] = StateDict(value, self._parent, self._state_name, self._path + [key])
            elif isinstance(value, list):
                self._data[key] = StateList(value, self._parent, self._state_name, self._path + [key])
            else:
                # For scalar values, update the value in memory
                self._data[key] = value
                
                # Create directory and update value file
                if self._parent and self._state_name:
                    key_dir = os.path.join(self._get_dir_path(), safe_path_component(key))
                    os.makedirs(key_dir, exist_ok=True)
                    val_file = os.path.join(key_dir, 'val.json')
                    with open(val_file, 'w') as f:
                        json.dump(value, f)
        
        # Notify parent of changes
        if self._parent and self._state_name:
            self._parent._notify_change(self._state_name)

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __delitem__(self, key: str) -> None:
        if key in self._data:
            # Remove from memory
            del self._data[key]
            
            # Remove from file system
            if self._parent and self._state_name:
                key_dir = os.path.join(self._get_dir_path(), safe_path_component(key))
                if os.path.exists(key_dir):
                    shutil.rmtree(key_dir)
            
            # Notify parent of changes
            if self._parent and self._state_name:
                self._parent._notify_change(self._state_name)
        else:
            raise KeyError(key)

    def get(self, item, default=None):
        return self._data[item] if item in self._data else default

    def to_dict(self) -> Dict:
        result = {}
        for k, v in self._data.items():
            if isinstance(v, (StateDict, StateList)):
                result[k] = v.to_dict()
            else:
                result[k] = v
        return result

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return f"StateDict({self.to_dict()})"

    def __eq__(self, other) -> bool:
        if isinstance(other, dict):
            return self.to_dict() == other
        elif isinstance(other, StateDict):
            return self.to_dict() == other.to_dict()
        return False

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()


class StateList:
    """A wrapper for lists that provides automatic persistence"""

    def __init__(self, data: List = None, parent: '_State' = None, state_name: str = None, path: List[str] = None):
        self._data = []
        self._parent = parent
        self._state_name = state_name
        self._path = path or []
        
        # Create this directory first
        if self._parent and self._state_name:
            dir_path = self._get_dir_path()
            os.makedirs(dir_path, exist_ok=True)
            
            # Write type file
            type_file = os.path.join(dir_path, '__type.json')
            with open(type_file, 'w') as f:
                json.dump({"type": "list"}, f)
        
        # Then process data
        if data:
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    self._data.append(StateDict(item, parent, state_name, self._path + [str(i)]))
                elif isinstance(item, list):
                    self._data.append(StateList(item, parent, state_name, self._path + [str(i)]))
                else:
                    self._data.append(item)
                    # Persist scalar values immediately
                    if self._parent and self._state_name:
                        idx_dir = os.path.join(self._get_dir_path(), str(i))
                        os.makedirs(idx_dir, exist_ok=True)
                        val_file = os.path.join(idx_dir, 'val.json')
                        with open(val_file, 'w') as f:
                            json.dump(item, f)

    def _persist(self):
        """Save this StateList to the file system."""
        if not (self._parent and self._state_name):
            return
            
        # Get the directory path for this StateList
        dir_path = self._get_dir_path()
        
        # Create the directory if it doesn't exist
        os.makedirs(dir_path, exist_ok=True)
        
        # Write the type file indicating this is a list
        type_file_path = os.path.join(dir_path, '__type.json')
        with open(type_file_path, 'w') as f:
            json.dump({"type": "list"}, f)
        
        # Persist each value (nested objects will persist themselves)
        for i, v in enumerate(self._data):
            # Check if it's a container that will persist itself
            if isinstance(v, (StateDict, StateList)):
                continue
                
            # For scalar values, create a directory and value file
            idx_dir = os.path.join(dir_path, str(i))
            os.makedirs(idx_dir, exist_ok=True)
            
            val_file = os.path.join(idx_dir, 'val.json')
            with open(val_file, 'w') as f:
                json.dump(v, f)

    def _get_dir_path(self) -> str:
        """Get the directory path for this StateList."""
        if not self._parent or not self._state_name:
            return None
        
        # Start with the states directory
        dir_path = self._parent._states_dir
        
        # Build path from state name and additional path components
        components = [self._state_name] + self._path
        for component in components:
            dir_path = os.path.join(dir_path, safe_path_component(str(component)))
        
        return dir_path

    def __getitem__(self, idx: int) -> Any:
        return self._data[idx]

    def __setitem__(self, idx: int, value: Any) -> None:
        if isinstance(value, dict):
            self._data[idx] = StateDict(value, self._parent, self._state_name, self._path + [str(idx)])
        elif isinstance(value, list):
            self._data[idx] = StateList(value, self._parent, self._state_name, self._path + [str(idx)])
        else:
            # For scalar values, update the value in memory
            self._data[idx] = value
            
            # Create directory and update value file
            if self._parent and self._state_name:
                idx_dir = os.path.join(self._get_dir_path(), str(idx))
                os.makedirs(idx_dir, exist_ok=True)
                val_file = os.path.join(idx_dir, 'val.json')
                with open(val_file, 'w') as f:
                    json.dump(value, f)
        
        # Notify parent of changes
        if self._parent and self._state_name:
            self._parent._notify_change(self._state_name)

    def __contains__(self, value: Any) -> bool:
        return value in self._data

    def __len__(self) -> int:
        return len(self._data)

    def append(self, value: Any) -> None:
        idx = len(self._data)
        if isinstance(value, dict):
            self._data.append(StateDict(value, self._parent, self._state_name, self._path + [str(idx)]))
        elif isinstance(value, list):
            self._data.append(StateList(value, self._parent, self._state_name, self._path + [str(idx)]))
        else:
            # For scalar values, update the value in memory
            self._data.append(value)
            
            # Create directory and update value file
            if self._parent and self._state_name:
                idx_dir = os.path.join(self._get_dir_path(), str(idx))
                os.makedirs(idx_dir, exist_ok=True)
                val_file = os.path.join(idx_dir, 'val.json')
                with open(val_file, 'w') as f:
                    json.dump(value, f)
        
        # Notify parent of changes
        if self._parent and self._state_name:
            self._parent._notify_change(self._state_name)
        
    def extend(self, stuff):
        for st in stuff:
            self.append(st)

    def to_dict(self) -> List:
        result = []
        for item in self._data:
            if isinstance(item, (StateDict, StateList)):
                result.append(item.to_dict())
            else:
                result.append(item)
        return result

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return f"StateList({self.to_dict()})"

    def __eq__(self, other) -> bool:
        if isinstance(other, list):
            return self.to_dict() == other
        elif isinstance(other, StateList):
            return self.to_dict() == other.to_dict()
        return False


class _State:
    def __init__(self):
        import os
        suffixe = os.getenv('COGNI_STATE_SUFFIX')
        
        self._states_dir = f'./.states'
        self._cache = {}
        self._callbacks = []
        os.makedirs(self._states_dir, exist_ok=True)

    def reset_cache(self):
        """Clear the in-memory cache."""
        self._cache = {}

    def onChange(self, callback):
        """Set a callback to be triggered when state changes."""
        self._callbacks = [callback]

    def _notify_change(self, state_name: str):
        """Notify callbacks of a change to a state."""
        if state_name in self._cache:
            state_dict = self._cache[state_name].to_dict()
            for callback in self._callbacks:
                callback(state_name, state_dict)

    def _load_state_recursive(self, base_dir: str) -> Union[Dict, List, Any]:
        """
        Recursively load a state from a directory structure.
        
        Args:
            base_dir: The directory to load the state from
        
        Returns:
            The loaded state as a dictionary, list, or scalar value
        """
        # Check if this is a leaf node (has val.json)
        val_file = os.path.join(base_dir, 'val.json')
        if os.path.isfile(val_file):
            with open(val_file, 'r') as f:
                try:
                    toto = f.read()
                    return json.loads(toto)
                except json.JSONDecodeError:
                    return None
        
        # Check if this is a container node (has __type.json)
        type_file = os.path.join(base_dir, '__type.json')
        if os.path.isfile(type_file):
            with open(type_file, 'r') as f:
                try:
                    toto = f.read()
                    type_info = json.loads(toto)
                    container_type = type_info.get("type")
                    
                    # Process based on type
                    if container_type == "dict":
                        result = {}
                        for item in os.listdir(base_dir):
                            item_path = os.path.join(base_dir, item)
                            # Skip type file and non-directories
                            if item == '__type.json' or not os.path.isdir(item_path):
                                continue
                            result[item] = self._load_state_recursive(item_path)
                        return result
                    
                    elif container_type == "list":
                        # Create a list of appropriate size
                        result = []
                        indices = []
                        
                        # First, collect all valid indices
                        for item in os.listdir(base_dir):
                            item_path = os.path.join(base_dir, item)
                            # Skip type file and non-directories
                            if item == '__type.json' or not os.path.isdir(item_path):
                                continue
                            
                            # Try to convert the directory name to an integer index
                            try:
                                idx = int(item)
                                indices.append((idx, item_path))
                            except ValueError:
                                # Skip directories that don't convert to indices
                                continue
                        
                        # Sort indices and load values
                        indices.sort()
                        for idx, item_path in indices:
                            # Ensure list has enough items
                            while len(result) <= idx:
                                result.append(None)
                            result[idx] = self._load_state_recursive(item_path)
                        
                        # Filter out None values that might exist due to gaps
                        return [x for x in result if x is not None]
                    
                except json.JSONDecodeError:
                    return {}
        
        # Default: return empty dict
        return {}

    def _load_state(self, state_name: str) -> Dict:
        """Load a state by name from the file system."""
        # Check if the directory for this state exists
        state_dir = os.path.join(self._states_dir, state_name)
        if os.path.isdir(state_dir):
            # Load the state recursively
            return self._load_state_recursive(state_dir)
        
        # Legacy support - check for JSON file
        legacy_path = os.path.join(self._states_dir, f"{state_name}.json")
        if os.path.exists(legacy_path):
            with open(legacy_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        
        return {}

    def _save_state(self, state_name: str, data: Union[StateDict, Dict]) -> None:
        """
        Legacy method for backward compatibility.
        In the new hierarchical structure, persistence is handled by individual StateDict
        and StateList objects as they're modified.
        """
        if data and self._callbacks:
            data_dict = data.to_dict() if isinstance(data, (StateDict, StateList)) else data
            for callback in self._callbacks:
                callback(state_name, data_dict)

    def __getitem__(self, state_name: str) -> StateDict:
        """Get a state by name, loading it from disk if not in cache."""
        if state_name not in self._cache:
            data = self._load_state(state_name)
            self._cache[state_name] = StateDict(data, self, state_name)
        return self._cache[state_name]

    def __contains__(self, key):
        """Check if a state exists and is not empty."""
        return self[key].to_dict() != {}

    def __setitem__(self, state_name: str, value: Dict) -> None:
        """Set a state to a new value."""
        # Convert to StateDict if it's not already
        if isinstance(value, dict):
            self._cache[state_name] = StateDict(value, self, state_name)
        elif isinstance(value, list):
            self._cache[state_name] = StateList(value, self, state_name)
        else:
            # For scalar values, create a simple structure
            state_dir = os.path.join(self._states_dir, state_name)
            os.makedirs(state_dir, exist_ok=True)
            val_file = os.path.join(state_dir, 'val.json')
            with open(val_file, 'w') as f:
                json.dump(value, f)
            self._cache[state_name] = value
        
        # Notify callbacks
        if self._callbacks:
            data_dict = self._cache[state_name].to_dict() if hasattr(self._cache[state_name], 'to_dict') else self._cache[state_name]
            for callback in self._callbacks:
                callback(state_name, data_dict)

    def __delitem__(self, state_name: str) -> None:
        """Delete a state."""
        # Remove from cache
        self._cache.pop(state_name, None)
        
        # Remove from file system
        state_dir = os.path.join(self._states_dir, state_name)
        if os.path.isdir(state_dir):
            shutil.rmtree(state_dir)
        
        # Legacy support - remove JSON file if it exists
        legacy_path = os.path.join(self._states_dir, f"{state_name}.json")
        if os.path.exists(legacy_path):
            os.remove(legacy_path)


State = _State()
