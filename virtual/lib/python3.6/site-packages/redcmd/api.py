from redlib.api.misc import make_api, Move

moves = []

exclude = ['test', 'version', 'main', '__main__', '__init__']

make_api(__name__, __file__, exclude=exclude, moves=moves)

__path__ = []

__package__ = __name__  # see PEP 366 @ReservedAssignment
if globals().get("__spec__") is not None:
	 __spec__.submodule_search_locations = []  # PEP 451 @UndefinedVariable

