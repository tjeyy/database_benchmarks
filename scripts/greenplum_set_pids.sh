#!/bin/bash

pids=$(ps -ef | grep postgres | grep -o '[[:digit:]][[:digit:]][[:digit:]][[:digit:]][[:digit:]][[:digit:]][[:digit:]]')
for pid in $pids
do
    sudo echo "+${pid}" | sudo tee /cgroups_benchmark/greenplum/run/cgroup.procs
done
