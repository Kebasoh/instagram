__all__ = ['CommandError', 'CommandLineError']


class CommandError(Exception):
	pass


class CommandLineError(Exception):
	pass


class SubcommandError(Exception):
	pass


class MaincommandError(Exception):
	pass


class CommandCollectionError(Exception):
	pass



