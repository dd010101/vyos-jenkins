import json
from json import JSONDecodeError
import os


class Cache:
    _data = None
    _loaded = False

    def __init__(self, path, root_type, fallback):
        self.path = path
        self.root_type = root_type
        self.fallback = fallback

    def get(self, name, default=None, data_type=None, bypass_cache=False):
        data = self.load(bypass_cache)
        if name in data:
            value = data[name]
            if data_type is not None:
                try:
                    return data_type(value)
                except (TypeError, ValueError):
                    pass
            else:
                return value
        return default

    def set(self, name, value, flush=True, bypass_cache=False):
        data = self.load(bypass_cache)
        data[name] = value
        if flush:
            self.save(data)

    def callback(self, name, callback):
        data = self.load()
        if data and name in data:
            return data[name]

        data[name] = callback()
        self.save(data)
        return data[name]

    def load(self, bypass_cache=False):
        if not self._loaded or bypass_cache:
            if os.path.exists(self.path):
                with open(self.path, "r") as file:
                    try:
                        contents = json.load(file)
                        self._data = self.root_type(contents)
                        self._loaded = True
                    except (JSONDecodeError, TypeError, ValueError):
                        pass

            if not self._loaded:
                self._loaded = True
                self._data = self.fallback

        return self._data

    def flush(self):
        self.save(self.load())

    def save(self, contents):
        directory = os.path.dirname(self.path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(self.path, "w") as file:
            json.dump(contents, file, indent=True)

    def purge(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def clear_cache(self):
        self._loaded = False
        self._data = None
