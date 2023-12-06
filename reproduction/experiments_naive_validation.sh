#!/bin/bash

set -e

if [ $# -ne 1 ]; then
  echo 'Usage: ./experiments_naive_validation.sh NUMA_NODE'
  echo '  NUMA_NODE is the NUMA node ID to bind the experiments to.'
  exit 1
fi

node_id=$1

# Build and execute naive dependency discovery for comparison.
cd hyrise/cmake-build-release
git checkout benchmark-naive-validation
make hyriseBenchmarkTPCH hyriseBenchmarkTPCDS hyriseBenchmarkStarSchema hyriseBenchmarkJoinOrder \
     hyriseDependencyDiscoveryPlugin -j "$(nproc)"

# Validation times for naive dependency discovery.
cd ..
numactl -N "${node_id}" -m "${node_id}" SCHEMA_CONSTRAINTS=0 VALIDATION_LOOPS=100 ./cmake-build-release/hyriseBenchmarkTPCH \
    -r 0 -p ./cmake-build-release/lib/libHyriseDependencyDiscoveryPlugin.so \
    > cmake-build-release/benchmark_plugin_results/hyriseBenchmarkTPCH_st_s10_plugin_naive.log
numactl -N "${node_id}" -m "${node_id}" SCHEMA_CONSTRAINTS=0 VALIDATION_LOOPS=100 ./cmake-build-release/hyriseBenchmarkTPCDS \
    -r 0 -p ./cmake-build-release/lib/libHyriseDependencyDiscoveryPlugin.so \
    > cmake-build-release/benchmark_plugin_results/hyriseBenchmarkTPCDS_st_s10_plugin_naive.log
numactl -N "${node_id}" -m "${node_id}" SCHEMA_CONSTRAINTS=0 VALIDATION_LOOPS=100 ./cmake-build-release/hyriseBenchmarkStarSchema \
    -r 0 -p ./cmake-build-release/lib/libHyriseDependencyDiscoveryPlugin.so \
    > cmake-build-release/benchmark_plugin_results/hyriseBenchmarkStarSchema_st_s10_plugin_naive.log
numactl -N "${node_id}" -m "${node_id}" SCHEMA_CONSTRAINTS=0 VALIDATION_LOOPS=100 ./cmake-build-release/hyriseBenchmarkJoinOrder \
    -r 0 -p ./cmake-build-release/lib/libHyriseDependencyDiscoveryPlugin.so \
    > cmake-build-release/benchmark_plugin_results/hyriseBenchmarkJoinOrder_st_plugin_naive.log

git checkout main
