#!/bin/bash

set -e

if [ $# -ne 1 ]
then
  echo 'Please provide a git revision!.'
  echo 'Typical call (in a release build folder): ../scripts/benchmark_single_optimizations.sh HEAD'
  exit 1
fi

benchmarks='hyriseBenchmarkTPCH hyriseBenchmarkTPCDS hyriseBenchmarkStarSchema'
sf='10'
commit=$1

# Here comes the actual work
# Checkout and build from scratch, tracking the compile time
echo "$commit"

# Run the benchmarks
#cd ..  # hyriseBenchmarkJoinOrder needs to run from project root

for benchmark in $benchmarks
do
  echo "$benchmark"
  python3 hyrise/scripts/compare_benchmarks.py "benchmark_plugin_results/${benchmark}_${commit}_st_s${sf}_all_off.json" "benchmark_plugin_results/${benchmark}_8eac957fc795e53e775f4284dcfc173b00642b69_no_pruning_st_s${sf}_plugin.json" | grep Sum
  python3 hyrise/scripts/compare_benchmarks.py "benchmark_plugin_results/${benchmark}_${commit}_st_s${sf}_all_off.json" "benchmark_plugin_results/${benchmark}_8eac957fc795e53e775f4284dcfc173b00642b69_no_pruning_st_s${sf}_plugin_jtp.json" | grep Sum
  python3 hyrise/scripts/compare_benchmarks.py "benchmark_plugin_results/${benchmark}_${commit}_st_s${sf}_plugin.json" "benchmark_plugin_results/${benchmark}_8eac957fc795e53e775f4284dcfc173b00642b69_no_pruning_st_s${sf}_plugin.json" | grep Sum
done
  echo "hyriseBenchmarkJoinOrder"
  python3 hyrise/scripts/compare_benchmarks.py "benchmark_plugin_results/hyriseBenchmarkJoinOrder_${commit}_st_all_off.json" "benchmark_plugin_results/hyriseBenchmarkJoinOrder_8eac957fc795e53e775f4284dcfc173b00642b69_no_pruning_st_plugin.json" | grep Sum
  python3 hyrise/scripts/compare_benchmarks.py "benchmark_plugin_results/hyriseBenchmarkJoinOrder_${commit}_st_all_off.json" "benchmark_plugin_results/hyriseBenchmarkJoinOrder_8eac957fc795e53e775f4284dcfc173b00642b69_no_pruning_st_plugin_jtp.json" | grep Sum
  python3 hyrise/scripts/compare_benchmarks.py "benchmark_plugin_results/hyriseBenchmarkJoinOrder_${commit}_st_plugin.json" "benchmark_plugin_results/hyriseBenchmarkJoinOrder_8eac957fc795e53e775f4284dcfc173b00642b69_no_pruning_st_plugin.json" | grep Sum

exit 0
