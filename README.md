# Enabling Data Dependency-based Query Optimization

This repository contains the artifacts for the paper _Enabling Data Dependency-based Query Optimization_.

## Reproduction guide

We listed all steps required to compile the DBMS code and execute all experiments in `reproduction.sh` See this file for details, or execute it as is.

Reproducing all results will require multiple days. The script is expected to run on a recent Ubuntu version. See the usage in the following:
```
./reproduction.sh NUMA_NODE [CLIENTS]
```
  - `NUMA_NODE` is the NUMA node ID to bound the experiments to.
  - `CLIENTS` is the number of clients to use for the high-load experiments. Defaults to the number of cores' avaible on NUMA node `NUMA_NODE` * 0.6.

## Repository Structure

The `hyrise` submodule imports the adapted version of Hyrise for dependency-based query optimization.
- The presented query rewrites are implemented as optimizer rules, found in `hyrise/src/lib/optimizer/strategy`. The relevant implementations are:
  - O-1: `dependent_group_by_reduction_rule.[c|h]pp`
  - O-2: `join_to_semi_join_rule.[c|h]pp`
  - O-3: `join_to_predicate_rewrite_rule.[c|h]pp`
- `hyrise/src/plugins/dependency_discovery_plugin.[c|h]pp` contains the dependency discovery plug-in. The implementation is further split.
  - The `candidate_strategy` subdirectory contains the candidate generation rules.
  - The `validation_strategy` subdirectory contains the metadata-aware dependency validation algorithms.

The code to run experiments is mostly located in the `python` folder.

- `python/db_comparison_runner.py` executes the experiment that measures the throughput improvement for different DBMSs.

- `python/greenplum_configure.py` creates the required config files for the Greenplum DBMS.

The `resources` directory contains the benchmark schema/create table statements and log files.
Python scripts for visualization and helpers to setup and run Greenplum are located in `scripts`.
