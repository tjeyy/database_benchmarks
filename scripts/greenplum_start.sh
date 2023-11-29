#!/bin/bash

set -e

home_dir=$(readlink -e ~)
gp_home="${home_dir}/greenplum"

GPHOME="${gp_home}" numactl -C +0-+55 -m 2 "${gp_home}/bin/gpinitsystem" -c "$(pwd)/resources/greenplum_config.cfg" -m 300 -a -l "${home_dir}/gpAdminLogs"

# add users to database
echo local all all trust >> "${home_dir}/gp_data/gpseg-1/pg_hba.conf"
echo host all all samehost trust >> "${home_dir}/gp_data/gpseg-1/pg_hba.conf"
echo local all +users trust >> "${home_dir}/gp_data/gpseg-1/pg_hba.conf"
echo hostssl all +users samenet trust >> "${home_dir}/gp_data/gpseg-1/pg_hba.conf"

"${gp_home}/bin/psql" -p 7777 -d dbbench -f "$(pwd)/scripts/gp_create_users.sql"

# increase memory limit
PGPORT=7777 GPHOME="${gp_home}" COORDINATOR_DATA_DIRECTORY="${home_dir}/gp_data/gpseg-1"  "${gp_home}/bin/gpconfig" -c gp_vmem_protect_limit -v 50000

# reload config
GPHOME="${gp_home}" "${gp_home}/bin/gpstop" -d "${home_dir}/gp_data/gpseg-1" -u

"${gp_home}/bin/psql" -p 7777 -d dbbench -f "$(pwd)/scripts/gp_reload.sql"

# restart to apply all changes (esp. memory limit)
GPHOME="${gp_home}" "${gp_home}/bin/gpstop" -d "${home_dir}/gp_data/gpseg-1" -a
GPHOME="${gp_home}" "${gp_home}/bin/gpstart" -d "${home_dir}/gp_data/gpseg-1" -l "${home_dir}/gpAdminLogs" -a
