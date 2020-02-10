function _redcmd_autocomp_function()
{
	local comp_word=${COMP_WORDS[COMP_CWORD]}
	local comp_line=${COMP_LINE}

	if [[ "$comp_word" == -* ]]
	then
		comp_word=" $comp_word"
	fi

	options=($(redcmd autocomp gen "${comp_line}" "$comp_word" 2>/dev/null))
	
	if [[ ${#options[@]} -gt 0 ]] && [[ ${options[0]} =~ \/ ]]; then
	      compopt -o filenames
	fi

	if [ $? -eq 0 ]
	then
		COMPREPLY=("${options[@]}")
	fi
}

export -f _redcmd_autocomp_function
