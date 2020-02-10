from os.path import exists
from os import remove

from redlib.api.py23 import *


class SimpleCache:

        def __init__(self, filepath):
                self._filepath = filepath
                self.load()


        def load(self):
                self._map = {}

                if exists(self._filepath):
                        with open(self._filepath , 'rb') as f:
                                self._map = pickleload(f)


        def save(self):
                with open(self._filepath, 'wb') as f:
                        pickledump(self._map, f)


        def set(self, key, value, pickle=False):
                self._map[key] = value if not pickle else pickledumps(value)
                self.save()


        def get(self, key, default=None, pickle=False):
                value = self._map.get(key, default)
                return value if not pickle else pickleloads(value)


        def clear(self):
                if exists(self._filepath):
                        remove(self._filepath)
                self._map = {}
