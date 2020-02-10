from os.path import join as joinpath, expanduser

from redlib.api.system import is_linux

if is_linux():
	from os import getuid
else:
	getuid = lambda : 1


subcmd_attr 		= '__subcmd__'
maincmd_attr 		= '__maincmd__'
add_attr		= '__add__'
parser_func_attr	= '__func__'
action_filter_attr	= '__filter__'
action_hidden_attr	= '__hidden__'
moved_attr		= '__moved__'

subcmd_dest_suffix 	= 'subcommand'

prog			= 'program'
description		= 'A command line utility.'
version			= '0.0.0'

user_home		= expanduser('~')
data_dir_name		= '.redcmd'

data_dir		= None
autocomp_dir		= None
script_dir		= None
root_data_dir		= joinpath('/var/local', data_dir_name)
root_autocomp_dir	= joinpath('/var/local', data_dir_name, 'autocomp')

if is_linux() and getuid() == 0:
	data_dir		= root_data_dir
	autocomp_dir		= joinpath(root_data_dir, 'autocomp')
	#script_dir		= joinpath(user_home, 'scripts')
else:
	data_dir		= joinpath(user_home, data_dir_name)
	autocomp_dir		= joinpath(data_dir, 'autocomp')
	
script_dir		= joinpath(user_home, data_dir_name, 'scripts')

internal_subcmd		= 'redcmdinternal'
internal_dummy_cmdname	= 'redcmdinternalcmd'
prog_name		= 'redcmd'

autocomp_function	= '__redcmd_autocomp'

commandline_exc_exit_code = 1

