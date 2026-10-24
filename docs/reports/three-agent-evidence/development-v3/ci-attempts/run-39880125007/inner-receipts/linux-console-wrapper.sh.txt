#!/bin/sh
printf '\033c\033]0;%s\a' SIGHTBREAK
base_path="$(dirname "$(realpath "$0")")"
"$base_path/sightbreak.x86_64" "$@"
