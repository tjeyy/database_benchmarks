#!/bin/bash

pids=$(pgrep greenplum)
for pid in $pids
do
    echo "+${pid}" | tee /sys/fs/cgroup/greenplum/gpadmin/cgroup.procs
done


pids=$(pgrep postgres)
for pid in $pids
do
    echo "+${pid}" | tee /sys/fs/cgroup/greenplum/gpadmin/cgroup.procs
done
