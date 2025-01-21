#!/bin/bash

pids=$(pgrep greenplum)
for pid in $pids
do
    echo "+${pid}" | sudo tee /sys/fs/cgroup/greenplum/gpadmin/cgroup.procs > /dev/null
done


pids=$(pgrep postgres)
for pid in $pids
do
    echo "+${pid}" | sudo tee /sys/fs/cgroup/greenplum/gpadmin/cgroup.procs > /dev/null
done


pids=$(pgrep -u gpadmin)
for pid in $pids
do
    echo "+${pid}" | sudo tee /sys/fs/cgroup/greenplum/gpadmin/cgroup.procs > /dev/null
done
