from os.path import join as joinpath, exists, splitext, split, abspath
from os import remove, makedirs
from shutil import copy, move
from glob import glob

from redlib.api.misc import md5hash

from .simple_cache import SimpleCache
from .data_dir import DataDir
from . import config as g_config

#temp
def dbg(): import pdb; pdb.set_trace()


class FileCacheStrategy:
        LRU = 0


class FileCacheConfig:

        def __init__(self):
                self.strategy                   = FileCacheStrategy.LRU
                self.max                        = 50
                self.no_db                      = True
                self.datetime_suffix_fmt        = '_%Y_%m_%d_%H_%M_%S'
                self.prefix                     = 'cached'
                self.dirpath                    = None
                self.max_index                  = 10000
                self.max_size                   = None


        def hash(self):
                return md5hash(abspath(self.dirpath))    #todo: make abs


class FileCacheIndex:

        def __init__(self, key, start=0, max_index=10000):
                self._start = start
                self._key = key

                count_width = lambda n, c = 0 : c if n == 0 else count_width(int(n / 10), c + 1)
                width = count_width(max_index - 1)
                self._fmt = '%0' + str(width) + 'd'

                self.load()

        
        def load(self):
                data_dir = DataDir(g_config.home_dir_name)
                self._store = SimpleCache(joinpath(data_dir.fullpath, g_config.file_cache_index_store_filename))
                self._index = self._store.get(self._key) or self._start


        def clear(self):
                self._store.clear()


        def reset(self, start=None):
                self._index = start or self._start
                self.save()


        def save(self):
                self._store.set(self._key, self._index)


        def incr(self):
                index = self._index
                self._index += 1
                self.save()

                return self._fmt%index


        def get_index(self):
                return self._index


        def format(self, index):
                return self._fmt%index


        current_index = property(get_index)


class RollOverMap:

        def __init__(self, key):
                self._key = key
                self.load()


        def load(self):
                data_dir = DataDir(g_config.home_dir_name)
                self._store = SimpleCache(joinpath(data_dir.fullpath, g_config.file_cache_rollover_map))
                self._map = self._store.get(self._key) or []

        def save(self):
                self._store.set(self._key, self._map, pickle=True)


        def set(self, new_map):
                self._map = new_map
                self.save()


        def new(self, old_index):
                for o, n in self._map:
                        if o == old_index:
                                return n
                return None


        def remove(self, new_index):
                idx = None
                for (i, (o, n)) in enumerate(self._map):
                        if n == new_index:
                                idx = i
                                break
                if idx is not None:
                        del self._map[idx]
                        if len(self._map) == 0:
                                self.clear()
                        else:
                                self.save()


        def clear(self):
                self._store.clear()
                self._map = []


class FileCacheError(Exception):
        pass


class NoMostRecentFile(Exception):
        pass


class FileCache:

        def __init__(self, config=FileCacheConfig()):
                self._config = config
                self.check_config()

                self._index = FileCacheIndex(self._config.hash(), start=1, max_index=self._config.max_index)
                self._ro_map = RollOverMap(self._config.hash())

                self.check_dir()


        def check_config(self):
                if self._config.dirpath == None:
                        raise FileCacheError('bad config')


        def check_dir(self):
                if not exists(self._config.dirpath):
                        makedirs(self._config.dirpath)


        def add(self, src_filepath, ext=None):
                index = self.move_most_recent_file_down()

                if ext is None:
                        parts = splitext(split(src_filepath)[-1])
                        ext = parts[1][1:] if len(parts) > 1 else ''

                dest_filename = self._config.prefix \
                                + '.%s'%ext if (ext is not None and len(ext) > 0) else ''
                dest_filepath = joinpath(self._config.dirpath, dest_filename)

                copy(src_filepath, dest_filepath)

                self.check_max()
                index = self.check_for_rollover(int(index)) or index

                return index


        def check_max(self):
                cached_files = self.get_all_files()

                if len(cached_files) <= self._config.max:
                        return

                mr = self._config.prefix
                mr2 = mr + '_' + self._index.format(self._config.max_index)
                rem = 0

                n_cached_files = []
                for f in cached_files:
                        filename = split(f)[-1]
                        name = splitext(filename)[0]
                        if not (name == mr or name == mr2):
                                n_cached_files.append(f)
                        else:
                                rem += 1

                self.remove_multiple_files(sorted(n_cached_files, reverse=True)[self._config.max - rem : ])


        def move_most_recent_file_down(self):
                ext = None
                try:
                        _, ext = self.get_most_recent_file_name_ext()
                except NoMostRecentFile:
                        return self._index.current_index

                index = self._index.incr()
                dest_filename = self._config.prefix \
                                + '_' + index \
                                + '.%s'%ext if (ext is not None and len(ext) > 0) else ''
                dest_filepath = joinpath(self._config.dirpath, dest_filename)

                move(joinpath(self._config.dirpath, self._config.prefix + '.' + ext), dest_filepath)
                
                return int(index) + 1


        def check_for_rollover(self, index):
                if (index) > self._config.max_index:
                        self.rollover()
                        return self._index.current_index
                else:
                        return None


        def rollover(self):
                indices = self.get_all_indices()
                sorted_indices = sorted(indices)[1:]

                old_to_new_map = []
                for i, o in enumerate(sorted_indices):
                        filename = self._config.prefix + '_' + self._index.format(o)
                        fullpath = self.suffix_ext(filename)
                        ext = splitext(split(fullpath)[-1])[1]
                        
                        newname = self._config.prefix + '_' + self._index.format(i + 1) + ext
                        newpath = joinpath(self._config.dirpath, newname)

                        if not exists(newpath):
                                move(fullpath, newpath)
                                old_to_new_map.append((o, i + 1))

                self._ro_map.set(old_to_new_map)
                self._index.reset(start = old_to_new_map[-1][1] + 1)


        def get_most_recent_file_name_ext(self):
                for f in self.get_all_files():
                        name, ext = splitext(split(f)[-1])
                        if name == self._config.prefix:
                                return name, ext[1:]
                raise NoMostRecentFile()


        def get(self, index=None, rel_index=None):
                if index is not None:
                        index = self._ro_map.new(index) or index
                        if index > self._index.current_index:
                                raise FileCacheError('index greater than that of the last file added')

                        filename = None
                        if index == 0:
                                filename = self._config.prefix
                        else:
                                filename = self._config.prefix + '_' + self._index.format(index)

                        filepath = self.suffix_ext(filename)
                        
                        return filepath if (filepath and exists(filepath)) else None
                
                elif rel_index is not None:
                        cached_files = sorted(self.get_all_files())
                        index = -rel_index
                        if len(cached_files) > index:
                                return cached_files[index]
                        else:
                                return None

                else:
                        raise FileCacheError('cannot get a file without index or rel_index')


        def suffix_ext(self, name):
                cached_files = self.get_all_files(prefix=name)
                return cached_files[0] if len(cached_files) > 0 else None


        def get_all_files(self, prefix=None):
                prefix = prefix or self._config.prefix
                glob_path = joinpath(self._config.dirpath, prefix + '*')
                return glob(glob_path)


        def get_all_indices(self):
                cached_files = self.get_all_files()
                indices = []

                if any([splitext(split(f)[-1])[0] == self._config.prefix for f in cached_files]):
                        indices.append(0)

                indices.extend(map(lambda n : int(n.split('_')[1]),
                                filter(lambda n : n.find('_') > -1,
                                map(lambda f : splitext(split(f)[-1])[0], cached_files))))
                return indices


        def clear(self):
                cached_files = self.get_all_files()
                self.remove_multiple_files(cached_files)

                self._index.clear()
                self._ro_map.clear()


        def _get_index_from_filename(self, filename):
                index = None
                name_wo_ext = splitext(split(filename)[-1])[0]
                try:
                        index = int(name_wo_ext.split('_')[-1])
                except ValueError:
                        pass
                return index


        def remove_multiple_files(self, filepath_list):
                err_msg = ''
                for f in filepath_list:
                        try:
                                remove(f)
                                self._ro_map.remove(self._get_index_from_filename(f))
                        except (OSError, IOError) as e:
                                err_msg += e.message

                if len(err_msg) > 0:
                        raise FileCacheError(err_msg)


        def make_most_recent(self, index):
                filepath = self.get(index)
                if filepath is None:
                        raise FileCacheError('no file with given index')

                index = self.move_most_recent_file_down()

                ext = splitext(split(filepath)[-1])[1]
                newpath = joinpath(self._config.dirpath, self._config.prefix + ext)

                move(filepath, newpath)

                return index, newpath
