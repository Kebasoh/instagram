
from redlib.api.system import is_windows


home_dir_name = 'greencache' if is_windows() else '.greencache'
file_cache_index_store_filename = 'file_cache_indices'
file_cache_rollover_map = 'file_cache_rollover_maps'

test = False
