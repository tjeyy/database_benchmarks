#!/bin/bash

./python/db_comparison_runner.py hyrise --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark TPCH; 
./python/db_comparison_runner.py hyrise-int --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark TPCH; 
./python/db_comparison_runner.py hyrise --rewrites --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark TPCH;

./python/db_comparison_runner.py hyrise --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark TPCDS;
./python/db_comparison_runner.py hyrise-int --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark TPCDS;
./python/db_comparison_runner.py hyrise --rewrites --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark TPCDS;

./python/db_comparison_runner.py hyrise --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark SSB;
./python/db_comparison_runner.py hyrise-int --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark SSB;
./python/db_comparison_runner.py hyrise --rewrites --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark SSB;

./python/db_comparison_runner.py hyrise --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark JOB;
./python/db_comparison_runner.py hyrise-int --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark JOB;
./python/db_comparison_runner.py hyrise --rewrites --clients 32 --cores 56 -m 2 --hyrise_server_path ../hyrise/cmake-build-release -t 1800 --benchmark JOB;

./python/db_comparison_runner.py monetdb --clients 32 --cores 56 -m 2 -t 1800 --benchmark TPCH; 
./python/db_comparison_runner.py monetdb --rewrites --clients 32 --cores 56 -m 2 -t 1800 --benchmark TPCH --skip_data_loading;

./python/db_comparison_runner.py monetdb --clients 32 --cores 56 -m 2 -t 1800 --benchmark TPCDS --skip_data_loading;
./python/db_comparison_runner.py monetdb --rewrites --clients 32 --cores 56 -m 2 -t 1800 --benchmark TPCDS --skip_data_loading;

./python/db_comparison_runner.py monetdb --clients 32 --cores 56 -m 2 -t 1800 --benchmark SSB --skip_data_loading;
./python/db_comparison_runner.py monetdb --rewrites --clients 32 --cores 56 -m 2 -t 1800 --benchmark SSB --skip_data_loading;

./python/db_comparison_runner.py monetdb --clients 32 --cores 56 -m 2 -t 1800 --benchmark JOB --skip_data_loading;
./python/db_comparison_runner.py monetdb --rewrites --clients 32 --cores 56 -m 2 -t 1800 --benchmark JOB --skip_data_loading;

./python/db_comparison_runner.py umbra --clients 32 --cores 56 -m 2 -t 1800 --benchmark TPCH; 
./python/db_comparison_runner.py umbra --rewrites --clients 32 --cores 56 -m 2 -t 1800 --benchmark TPCH;

./python/db_comparison_runner.py umbra --clients 32 --cores 56 -m 2 -t 1800 --benchmark TPCDS;
./python/db_comparison_runner.py umbra --rewrites --clients 32 --cores 56 -m 2 -t 3600 --benchmark TPCDS;

./python/db_comparison_runner.py umbra --clients 32 --cores 56 -m 2 -t 1800 --benchmark SSB;
./python/db_comparison_runner.py umbra --rewrites --clients 32 --cores 56 -m 2 -t 1800 --benchmark SSB;

./python/db_comparison_runner.py umbra --clients 32 --cores 56 -m 2 -t 1800 --benchmark JOB;
./python/db_comparison_runner.py umbra --rewrites --clients 32 --cores 56 -m 2 -t 1800 --benchmark JOB;
