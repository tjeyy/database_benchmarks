#!/bin/bash

set -e

home_dir=$(readlink -e ~)
echo "$home_dir"
gp_home="${home_dir}/greenplum"
echo "$gp_home"

GPHOME="${gp_home}" "${gp_home}/bin/gpstop" -a -d "${home_dir}/gp_data/gpseg-1"
