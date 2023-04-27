#!/bin/bash

output=$(flake8 --max-line-length 120 --exclude python/heplers/static_tpch_queries.py python)
if [ -n "$output" ]; then
	echo "$output"
	exitcode=1
fi

shellcheck scripts/*.sh

exit $exitcode
