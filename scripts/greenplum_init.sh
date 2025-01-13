#!/bin/bash

set -e

gp_home="$(pwd)/db_comparison_data/greenplum"

rm -rf "${gp_home}/data"
rm -rf "${gp_home}/logs"

mkdir "${gp_home}/data"
mkdir "${gp_home}/logs"

GPHOME="${gp_home}" "${gp_home}/bin/gpinitsystem" -c "$(pwd)/resources/greenplum_config.cfg" -m 300 -a -l "${gp_home}/logs"

./scripts/greenplum_configure.sh
