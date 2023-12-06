#!/bin/bash

output=$(flake8 --max-line-length 120 --exclude python/queries python scripts)
if [ -n "$output" ]; then
	echo "$output"
	exitcode=1
fi

shellcheck scripts/*.sh reproduction.sh reproduction/*.sh

exit $exitcode
