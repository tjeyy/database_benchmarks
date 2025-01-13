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
# https://techdocs.broadcom.com/us/en/vmware-tanzu/data-solutions/tanzu-greenplum/7/greenplum-database/best_practices-sysconfig.html
# gp_vmem = ((SWAP + RAM) – (7.5GB + 0.05 * RAM)) / 1.17  --> RAM = 370GB, SWAP = 8 GB
# gp_vmem approx. 300 GB
# gp_vmem_protect_limit = gp_vmem / max_acting_primary_segments  --> 27 segments
# gp_vmem_protect_limit = 11.11... GiB --> 11378 MiB
PGPORT=${PORT} GPHOME="${gp_home}" COORDINATOR_DATA_DIRECTORY="${gp_home}/data/gpseg-1"  "${gp_home}/bin/gpconfig" -c gp_vmem_protect_limit -v 21943

# Reload config.
GPHOME="${gp_home}" "${gp_home}/bin/gpstop" -d "${gp_home}/data/gpseg-1" -u

"${gp_home}/bin/psql" -p "${PORT}" -d dbbench -f "$(pwd)/scripts/gp_reload.sql"

# Restart to apply all changes (esp. memory limit).
GPHOME="${gp_home}" "${gp_home}/bin/gpstop" -a -d "${gp_home}/data/gpseg-1" -r


# We observed that changing the memory limit on all segments can require multiple restarts to be effective.
while ! PGPORT=${PORT} GPHOME="${gp_home}" COORDINATOR_DATA_DIRECTORY="${gp_home}/data/gpseg-1"  "${gp_home}/bin/gpconfig" -s gp_vmem_protect_limit | grep "Values on all segments are consistent"; do
  echo "Restart to set memory limit ..."
  sleep 5
  GPHOME="${gp_home}" "${gp_home}/bin/gpstop" -a -d "${gp_home}/data/gpseg-1" -r
done
