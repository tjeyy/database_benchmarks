#!/usr/bin/python3

import argparse as ap
import os
import socket


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, default=5432)
    # Greenplum recommends one partition per logical CPU core, but we encountered various problems with more partitions.
    parser.add_argument("--num_partitions", "-n", type=int, default=14)
    return parser.parse_args()


def main(port, num_partitions):
    hostname = socket.gethostname()
    host_file = os.path.join(os.getcwd(), "resources", "greenplum_hostfile.cfg")
    config_file = os.path.join(os.getcwd(), "resources", "greenplum_config.cfg")

    with open(host_file, "w") as f:
        f.write(f"{hostname}\n")

    gp_data_dir = os.path.join(os.getcwd(), "db_comparison_data", "greenplum", "data")
    with open(config_file, "w") as f:
        f.write("SEG_PREFIX=gpseg\n")
        f.write(f"PORT_BASE={args.port + 1}\n")
        f.write(f"declare -a DATA_DIRECTORY=({gp_data_dir})\n")
        f.write(f"COORDINATOR_HOSTNAME={hostname}\n")
        f.write(f"COORDINATOR_DIRECTORY={gp_data_dir}\n")
        f.write(f"COORDINATOR_PORT={args.port}\n")
        f.write("TRUSTED_SHELL=ssh\n")
        f.write("ENCODING=UNICODE\n")
        f.write("DATABASE_NAME=dbbench\n")
        f.write(f"MACHINE_LIST_FILE={host_file}\n")


if __name__ == "__main__":
    args = parse_args()
    main(args.port, args.num_partitions)
