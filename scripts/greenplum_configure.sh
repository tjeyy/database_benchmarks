#!/bin/bash

set -e

gp_home="$(pwd)/db_comparison_data/greenplum"

# Add users to database.
{
  echo local all all trust
  echo host all all samehost trust
  echo local all +users trust
  echo hostssl all +users samenet trust
} >> "${gp_home}/data/gpseg-1/pg_hba.conf"

"${gp_home}/bin/psql" -p "${PORT}" -d dbbench -f "$(pwd)/scripts/gp_create_users.sql"

# Increase memory limit.
PGPORT=${PORT} GPHOME="${gp_home}" COORDINATOR_DATA_DIRECTORY="${gp_home}/data/gpseg-1"  "${gp_home}/bin/gpconfig" -c gp_vmem_protect_limit -v 200000

# Reload config.
GPHOME="${gp_home}" "${gp_home}/bin/gpstop" -d "${gp_home}/data/gpseg-1" -u

"${gp_home}/bin/psql" -p "${PORT}" -d dbbench -f "$(pwd)/scripts/gp_reload.sql"

# Restart to apply all changes (esp. memory limit).
./scripts/greenplum_restart.sh


# We observed that changing the memory limit on all segments can require multiple restarts to be effective.
while ! PGPORT=${PORT} GPHOME="${gp_home}" COORDINATOR_DATA_DIRECTORY="${gp_home}/data/gpseg-1"  "${gp_home}/bin/gpconfig" -s gp_vmem_protect_limit; do
  ./scripts/greenplum_restart.sh
done
