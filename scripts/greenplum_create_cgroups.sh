#!/bin/bash

sudo mkdir -p /cgroups_benchmark
sudo mount -t cgroup2 none /cgroups_benchmark
sudo mkdir greenplum
cd greenplum || exit 1
sudo echo "+cpuset" | sudo tee cgroup.subtree_control
echo "56-83,168-195" | sudo tee cpuset.cpus
echo 2 | sudo tee cpuset.mems

sudo mkdir run
cd run || exit 2
sudo echo "+cpuset" | sudo tee cgroup.subtree_control
echo "56-83,168-195" | sudo tee cpuset.cpus
echo 2 | sudo tee cpuset.mems


sudo useradd gpadmin -r -m -g gpadmin
sudo chsh gpadmin -s /bin/bash
sudo passwd -d gpadmin

cd ..
sudo mkdir run
cd run || exit 2
sudo echo "+cpuset" | sudo tee cgroup.subtree_control
echo "56-83,168-195" | sudo tee cpuset.cpus
echo 2 | sudo tee cpuset.mems
sudo chown -R gpadmin:gpadmin .
sudo chmod a+w cgroup.procs
