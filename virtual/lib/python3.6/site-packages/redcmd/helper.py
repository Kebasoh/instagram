import types


def get_func(f, cmd_cls):
	'Additional param functions can be either function(s) or their names in str form.'

	if type(f) == types.FunctionType or type(f) == types.MethodType:
		func = f
	elif type(f) == str:
		if cmd_cls is not None:
			func = getattr(cmd_cls, f)
		else:
			func = getattr(vars(), f)
	else:
		func = None

	return func

