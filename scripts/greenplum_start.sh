#!/bin/bash

set -e

home_dir=$(readlink -e ~)
gp_home="${home_dir}/greenplum"

GPHOME="${gp_home}" "${gp_home}/bin/gpstart" -d "${home_dir}/gp_data/gpseg-1" -l "${home_dir}/gpAdminLogs" -a
