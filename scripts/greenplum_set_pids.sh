#!/bin/bash

pids=$(pgrep greenplum)
for pid in $pids
do
    sudo echo "+${pid}" | sudo tee cgroup.procs
done


pids=$(pgrep postgres)
for pid in $pids
do
    sudo echo "+${pid}" | sudo tee cgroup.procs
done
