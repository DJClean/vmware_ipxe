#!/bin/bash

# Created by argbash-init v2.7.1
# ARG_POSITIONAL_SINGLE([iso],[ISO file containing a VMware installation])
# ARG_POSITIONAL_SINGLE([name],[Name the new version should have for PXE/Web])
# ARG_POSITIONAL_SINGLE([destination],[Destination folder, reacheable using a Web client (Without trailing /)])
# ARG_DEFAULTS_POS([])
# ARG_HELP([Script used to add a new version to the PXE menu])
# ARGBASH_GO()
# needed because of Argbash --> m4_ignore([
### START OF CODE GENERATED BY Argbash v2.7.1 one line above ###
# Argbash is a bash code generator used to get arguments parsing right.
# Argbash is FREE SOFTWARE, see https://argbash.io for more info


die()
{
	local _ret=$2
	test -n "$_ret" || _ret=1
	test "$_PRINT_HELP" = yes && print_help >&2
	echo "$1" >&2
	exit ${_ret}
}


begins_with_short_option()
{
	local first_option all_short_options='h'
	first_option="${1:0:1}"
	test "$all_short_options" = "${all_short_options/$first_option/}" && return 1 || return 0
}

# THE DEFAULTS INITIALIZATION - POSITIONALS
_positionals=()
_arg_iso=
_arg_name=
_arg_destination=
# THE DEFAULTS INITIALIZATION - OPTIONALS


print_help()
{
	printf '%s\n' "Script used to add a new version to the PXE menu"
	printf 'Usage: %s [-h|--help] <iso> <name> <destination>\n' "$0"
	printf '\t%s\n' "<iso>: ISO file containing a VMware installation"
	printf '\t%s\n' "<name>: Name the new version should have for PXE/Web"
	printf '\t%s\n' "<destination>: Destination folder, reacheable using a Web client"
	printf '\t%s\n' "-h, --help: Prints help"
}


parse_commandline()
{
	_positionals_count=0
	while test $# -gt 0
	do
		_key="$1"
		case "$_key" in
			-h|--help)
				print_help
				exit 0
				;;
			-h*)
				print_help
				exit 0
				;;
			*)
				_last_positional="$1"
				_positionals+=("$_last_positional")
				_positionals_count=$((_positionals_count + 1))
				;;
		esac
		shift
	done
}


handle_passed_args_count()
{
	local _required_args_string="'iso', 'name' and 'destination'"
	test "${_positionals_count}" -ge 3 || _PRINT_HELP=yes die "FATAL ERROR: Not enough positional arguments - we require exactly 3 (namely: $_required_args_string), but got only ${_positionals_count}." 1
	test "${_positionals_count}" -le 3 || _PRINT_HELP=yes die "FATAL ERROR: There were spurious positional arguments --- we expect exactly 3 (namely: $_required_args_string), but got ${_positionals_count} (the last one was: '${_last_positional}')." 1
}


assign_positional_args()
{
	local _positional_name _shift_for=$1
	_positional_names="_arg_iso _arg_name _arg_destination "

	shift "$_shift_for"
	for _positional_name in ${_positional_names}
	do
		test $# -gt 0 || break
		eval "$_positional_name=\${1}" || die "Error during argument parsing, possibly an Argbash bug." 1
		shift
	done
}

parse_commandline "$@"
handle_passed_args_count
assign_positional_args 1 "${_positionals[@]}"

# OTHER STUFF GENERATED BY Argbash

### END OF CODE GENERATED BY Argbash (sortof) ### ])
# [ <-- needed because of Argbash

if [ ! -f "${_arg_iso}" ]
then
  die "ERROR: ISO file does not exist (ISO: ${_arg_iso})" 1
fi

if [ ! -d "${_arg_destination}" ]
then
  die "ERROR: Destination directory does not exist or is a file (Destination: ${_arg_destination})" 1
fi

if [ -d "${_arg_destination}/${_arg_name}" ]
then
 die "ERROR: Directory with ${_arg_name} already exists in destination. Cancelling" 1
else
  mkdir "${_arg_destination}/${_arg_name}" || die "ERROR: Failed to create directory" 1
fi

_temp_dir=$(mktemp -d)

mount -o loop "${_arg_iso}" "${_temp_dir}"

# Check if VMware iso

if [ ! -f "${_temp_dir}/tboot.b00" ]
then
  umount "${_temp_dir}"
  die "ERROR: This doesn't look like a VMware ISO" 1
fi

rsync -a "${_temp_dir}/" "${_arg_destination}/${_arg_name}"

cp -pr "${_arg_destination}/${_arg_name}/efi/boot/bootx64.efi" "${_arg_destination}/${_arg_name}/mboot.efi"

sed -i 's/\///g' "${_arg_destination}/${_arg_name}/boot.cfg"

umount "${_temp_dir}"

echo "New version with name ${_arg_name} has been added to the repository in ${_arg_destination}"

# ] <-- needed because of Argbash