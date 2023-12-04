#!/bin/bash

set -e

home_dir=$(readlink -e ~)
gp_home="${home_dir}/greenplum"

rm -rf ~/gp_data
rm -rf ~/gpAdminLogs

mkdir ~/gp_data
mkdir ~/gpAdminLogs

GPHOME="${gp_home}" "${gp_home}/bin/gpinitsystem" -c "$(pwd)/resources/greenplum_config.cfg" -m 300 -a -l "${home_dir}/gpAdminLogs"

./scripts/greenplum_configure.sh
