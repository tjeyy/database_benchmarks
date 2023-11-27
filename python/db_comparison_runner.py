#!/usr/bin/python3
# Thanks to Markus Dreseler, who initially built this script, and Martin Boissier, who extended it.

import argparse
import atexit
import json
import os
import random
import shutil
import socket
import statistics
import struct
import subprocess
import sys
import threading
import time
from pathlib import Path

import pandas as pd
from queries import static_job_queries, static_ssb_queries, static_tpcds_queries, static_tpch_queries

# For a fair comparison, we use the same queries as the Umbra demo does.
tpch_queries = static_tpch_queries.queries
ssb_queries = static_ssb_queries.queries


def query_blacklist(filename):
    blacklist = set()
    with open(filename) as f:
        for line in f:
            if not line.startswith("#"):
                blacklist.add(line.strip())
    return blacklist


def load_queries(dir, blacklist={}):
    queries = {}
    for filename in Path(dir).glob("*.sql"):
        if not filename.is_file() or filename.name in blacklist:
            continue

        with open(str(filename), "r") as sql_file:
            sql_query = sql_file.read()
            queries[filename.stem] = sql_query.strip()
    return queries


job_queries = load_queries("hyrise/third_party/join-order-benchmark", {"fkindexes.sql", "schema.sql"})
tpcds_path = "hyrise/resources/benchmark/tpcds"
tpcds_blacklist = query_blacklist(os.path.join(tpcds_path, "query_blacklist.cfg"))
tpcds_queries = load_queries(os.path.join(tpcds_path, "tpcds-result-reproduction/query_qualification"), tpcds_blacklist)


# gather size information
tables = {
    "JOB": [
        "aka_name",
        "aka_title",
        "cast_info",
        "char_name",
        "comp_cast_type",
        "company_name",
        "company_type",
        "complete_cast",
        "info_type",
        "keyword",
        "kind_type",
        "link_type",
        "movie_companies",
        "movie_info",
        "movie_info_idx",
        "movie_keyword",
        "movie_link",
        "name",
        "person_info",
        "role_type",
        "title",
    ],
    "TPC-H": ["nation", "region", "part", "supplier", "partsupp", "customer", "orders", "lineitem"],
    "TPC-DS": [
        "call_center",
        "catalog_page",
        "catalog_returns",
        "catalog_sales",
        "customer",
        "customer_address",
        "customer_demographics",
        "date_dim",
        "household_demographics",
        "income_band",
        "inventory",
        "item",
        "promotion",
        "reason",
        "ship_mode",
        "store",
        "store_returns",
        "store_sales",
        "time_dim",
        "warehouse",
        "web_page",
        "web_returns",
        "web_sales",
        "web_site",
    ],
    "SSB": ["customer", "date", "lineorder", "part", "supplier"],
}

"""
shared table names
TPC-H SSB {'supplier', 'customer', 'part'}
TPC-DS SSB {'customer'}
"""

parser = argparse.ArgumentParser()
parser.add_argument("dbms", type=str, choices=["monetdb", "hyrise", "greenplum", "umbra", "hana", "hyrise-int"])
parser.add_argument("--time", "-t", type=int, default=300)
parser.add_argument("--port", "-p", type=int, default=5432)
parser.add_argument("--clients", type=int, default=1)
parser.add_argument("--cores", type=int, default=1)
parser.add_argument("--memory_node", "-m", type=int, default=2)
parser.add_argument("--benchmark", "-b", type=str, default="all", choices=["TPCH", "TPCDS", "JOB", "SSB", "all"])
parser.add_argument("--hyrise_server_path", type=str, default="hyrise/cmake-build-release")
parser.add_argument("--skip_warmup", action="store_true")
parser.add_argument("--skip_data_loading", action="store_true")
parser.add_argument("--rewrites", action="store_true")
args = parser.parse_args()

if args.dbms in ["hyrise", "hyrise-int"]:
    hyrise_server_path = Path(args.hyrise_server_path).expanduser().resolve()
    assert (hyrise_server_path / "hyriseServer").exists(), "Please pass valid --hyrise_server_path"

# monetdb_scale_factor_string = str(args.scale_factor).replace(".", "_")
# duckdb_scale_factor_string = int(args.scale_factor) if args.scale_factor >= 1.0 else args.scale_factor

assert (
    args.clients == 1 or args.time >= 300
), "When multiple clients are set, a shuffled run is initiated which should last at least 300s."

dbms_process = None

if args.dbms == "hana":
    tpch_queries.update(static_tpch_queries.hana_queries)
    job_queries.update(static_job_queries.hana_queries)
    ssb_queries.update(static_ssb_queries.umbra_queries)
elif args.dbms == "umbra":
    ssb_queries.update(static_ssb_queries.umbra_queries)

if args.rewrites:
    tpch_queries.update(static_tpch_queries.queries_o1)
    tpch_queries.update(static_tpch_queries.queries_o3)
    ssb_queries.update(static_ssb_queries.queries_o3)
    job_queries.update(static_job_queries.queries_o3)
    tpcds_queries.update(static_tpcds_queries.queries_o1)
    tpcds_queries.update(static_tpcds_queries.queries_o3)

    if args.dbms == "hana":
        tpch_queries.update(static_tpch_queries.hana_queries_o1)
        tpch_queries.update(static_tpch_queries.hana_queries_o3)
        job_queries.update(static_job_queries.hana_queries_o3)
        ssb_queries.update(static_ssb_queries.umbra_queries_o3)
    elif args.dbms == "umbra":
        ssb_queries.update(static_ssb_queries.umbra_queries_o3)

tpch_queries = list(tpch_queries.values())
tpcds_queries = list(tpcds_queries.values())
ssb_queries = list(ssb_queries.values())
job_queries = list(job_queries.values())

assert len(tpch_queries) == 22
assert len(tpcds_queries) == 48
assert len(ssb_queries) == 13
assert len(job_queries) == 113


def cleanup():
    if dbms_process:
        print("Shutting {} down...".format(args.dbms))
        dbms_process.kill()
        time.sleep(10)


atexit.register(cleanup)

print("Starting {}...".format(args.dbms))
if args.dbms == "monetdb":
    import pymonetdb

    subprocess.Popen(["pkill", "-9", "mserver5"])
    time.sleep(5)
    cmd = [
        "numactl",
        "-C",
        f"+0-+{args.cores - 1}",
        "-m",
        str(args.memory_node),
        "{}/monetdb_bin/bin/mserver5".format(Path.home()),
        "--dbpath={}/monetdb_farm".format(Path.home()),
        "--set",
        "gdk_nr_threads={}".format(args.cores),
    ]

    if args.clients > 62:
        cmd.extend(["--set", f"max_clients={args.clients + 2}"])
    if args.clients < 33:
        # We have seen strange errors when using the inmemory option and 64 clients (bat file not existing)
        cmd.append("--dbextra=inmemory")
    dbms_process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    while True:
        line = dbms_process.stdout.readline()
        if b"MonetDB/SQL module loaded" in line:
            break
elif args.dbms in ["hyrise", "hyrise-int"]:
    import psycopg2

    dbms_process = subprocess.Popen(
        [
            "numactl",
            "-C",
            "+0-+{}".format(args.cores - 1),
            "-m",
            str(args.memory_node),
            "{}/hyriseServer".format(hyrise_server_path),
            "-p",
            str(args.port),
        ],
        stdout=subprocess.PIPE,
    )
    time.sleep(5)
    while True:
        line = dbms_process.stdout.readline()
        if b"Server started at" in line:
            break
elif args.dbms == "umbra":
    import psycopg2

    parallel_dir = {"PARALLEL": "off"} if args.cores == 1 else {"PARALLEL": str(args.cores)}
    dbms_process = subprocess.Popen(
        [
            "numactl",
            "-C",
            "+0-+{}".format(args.cores - 1),
            "-m",
            str(args.memory_node),
            "{}/umbra/bin/server".format(Path.home()),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=parallel_dir,
    )
    print("Waiting 10s for Umbra to start ... ", end="")
    time.sleep(10)
    print("done.")
elif args.dbms == "greenplum":
    import psycopg2

    hostname = socket.gethostname()
    host_file = os.path.join(os.getcwd(), "resources", "greenplum_hostfile.cfg")
    config_file = os.path.join(os.getcwd(), "resources", "greenplum_config.cfg")

    with open(host_file, "w") as f:
        f.write(hostname)

    gp_data_dir = os.path.join(Path.home(), "gp_data")
    with open(config_file, "w") as f:
        f.write("SEG_PREFIX=gpseg")
        f.write(f"PORT_BASE={args.port + 1}")
        f.write(f"declare -a DATA_DIRECTORY=({gp_data_dir})")
        f.write(f"COORDINATOR_HOSTNAME={hostname}")
        f.write(f"COORDINATOR_DIRECTORY={gp_data_dir}")
        f.write(f"COORDINATOR_PORT={args.port}")
        f.write("TRUSTED_SHELL=ssh")
        f.write("ENCODING=UNICODE")
        f.write("DATABASE_NAME=dbbench")
        f.write(f"MACHINE_LIST_FILE={host_file}")

    if os.path.isdir(gp_data_dir):
        shutil.rmtree(gp_data_dir)
    os.makedirs(gp_data_dir)

    gp_home = os.path.join(Path.home(), "greenplum")
    dbms_process = subprocess.Popen(
        [
            "numactl",
            "-C",
            "+0-+{}".format(args.cores - 1),
            "-m",
            str(args.memory_node),
            os.path.join(gp_home, "bin", "gpinitsystem"),
            "-B",
            "1",
            "-c",
            host_file,
            "-m",
            str(args.clients),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"GPHOME", gp_home},
    )


def get_cursor():
    if args.dbms == "monetdb":
        connection = None
        while connection is None:
            try:
                connection = pymonetdb.connect("", connect_timeout=600, autocommit=True)
            except Exception as e:
                print(e)
                time.sleep(1)
                raise e
        connection.settimeout(600)
    elif args.dbms in ["hyrise", "hyrise-int"]:
        connection = psycopg2.connect("host=localhost port={}".format(args.port), autocommit=True)
    elif args.dbms == "umbra":
        connection = psycopg2.connect(host="/tmp", user="postgres")
    elif args.dbms == "greenplum":
        connection = psycopg2.connect(f"host=localhost port={args.port} dbname=dbbench")

    elif args.dbms == "hana":
        from hdbcli import dbapi

        with open("resources/database_connection.json", "r") as file:
            connection_data = json.load(file)
        connection = dbapi.connect(
            address=connection_data["host"],
            port=connection_data["port"],
            user=connection_data["db_user"],
            password=connection_data["db_user_password"],
            encrypt=True,
            sslValidateCertificate=False,
            autocommit=connection_data["autocommit"],
        )

    cursor = connection.cursor()
    return (connection, cursor)


def parse_data_type(type_string):
    if type_string == "int":
        return "Int32"
    elif type_string == "long":
        return "Int64"
    elif type_string == "float":
        return "Float32"
    elif type_string == "double":
        return "Float64"
    elif type_string == "string":
        return "string"
    raise AttributeError(f"Unknown data type: '{type_string}'")


def parse_csv_meta(meta):
    column_names = list()
    column_data_types = dict()
    nullable = dict()
    for column_meta in meta["columns"]:
        column_name = column_meta["name"]
        column_names.append(column_name)
        column_data_types[column_name] = parse_data_type(column_meta["type"])
        nullable[column_name] = column_meta["nullable"]
    return column_names, column_data_types, nullable


def import_data():
    data_path = os.path.join(os.getcwd(), "resources/experiment_data")
    table_files = sorted([f for f in os.listdir(data_path) if f.endswith(".csv") and ".umbra." not in f])

    if args.dbms == "monetdb":
        load_command = """COPY INTO "{}" FROM '{}' USING DELIMITERS ',', '\n', '"' NULL AS '';"""
    elif args.dbms in ["hyrise", "hyrise-int"]:
        load_command = """COPY "{}" FROM '{}';"""
    elif args.dbms == "umbra":
        load_command = """COPY "{}" FROM '{}' WITH DELIMITER ',' NULL '';"""
    elif args.dbms == "greenplum":
        load_command = """COPY "{}" FROM '{}' WITH (FORMAT CSV, DELIMITER ',', NULL '', QUOTE '"');"""
    elif args.dbms == "hana":
        load_command = """IMPORT FROM CSV FILE '{}' INTO {} WITH FIELD DELIMITED BY ',';"""

    connection, cursor = get_cursor()
    print("- Loading data ...")

    if args.dbms not in ["hyrise", "hyrise-int"]:
        for benchmark in ["tpch", "job", "ssb", "tpcds"]:
            with open(f"resources/schema_{benchmark}.sql") as f:
                for line in f:
                    stripped_line = line.strip()
                    if not stripped_line:
                        continue
                    if args.dbms == "hana":
                        cursor.execute(line.replace("text", "nvarchar(1024)"))
                    else:
                        cursor.execute(stripped_line)

    if args.dbms == "hana":
        cursor.execute(
            "alter system alter configuration ('indexserver.ini','SYSTEM') set "
            "('import_export','enable_csv_import_path_filter') = 'false' with reconfigure;"
        )

    for t_id, table_file in enumerate(table_files):
        table_name = table_file[: -len(".csv")]
        table_file_path = f"{data_path}/{table_file}"
        print(f" - ({t_id + 1}/{len(table_files)}) Import {table_name} from {table_file_path}", end=" ")
        start = time.time()

        if args.dbms == "monetdb" and table_name in tables["JOB"]:
            # MonetDB does not like some IMDB CSV files, so we encode them in their binary format.
            binary_data_types = {"Int32": "<i", "Int64": "<q"}
            with open(table_file_path + ".json") as f:
                meta = json.load(f)
            column_names, column_types, nullable = parse_csv_meta(meta)
            data = pd.read_csv(
                table_file_path, header=None, names=column_names, dtype=column_types, keep_default_na=False
            )
            all_column_files = list()
            for column_name in column_names:
                t_id = 0
                binary_file_path = f"{data_path}/{table_name}.{column_name}.bin"
                all_column_files.append(f"'{binary_file_path}'")

                if not os.path.isfile(binary_file_path):
                    with open(binary_file_path, "wb") as f:
                        if column_types[column_name] == "string":
                            for value in data[column_name].values:
                                t_id = t_id + 1
                                if pd.isna(value):
                                    assert nullable[column_name], f"{column_name} NULL in L{t_id}"
                                    f.write(b"\x80")
                                else:
                                    f.write(value.encode())
                                f.write(b"\x00")
                        else:
                            binary_type = binary_data_types[column_types[column_name]]
                            s = struct.Struct(binary_type)
                            for value in data[column_name].values:
                                t_id = t_id + 1
                                if pd.isna(value):
                                    assert nullable[column_name], f"{column_name} NULL in L{t_id}"
                                    assert column_types[column_name] == "Int32"
                                    f.write(b"\x00\x00\x00\x80")
                                else:
                                    f.write(s.pack(value))

                cursor.execute(
                    """COPY LITTLE ENDIAN BINARY INTO "{}" FROM {} ON SERVER;""".format(
                        table_name, ", ".join(all_column_files)
                    )
                )

        elif args.dbms == "umbra":  # and table_name in tables["JOB"]:
            # Umbra seems to have issues as well, so we rewrite the CSVs with '|' or '\r' as delimiter (which is an
            # ASCII character that does not occur in any file).
            new_file_path = f"{data_path}/{table_name}.umbra.csv"
            sep = "|" if table_name not in ["movie_info", "person_info"] else "\r"
            if not os.path.isfile(new_file_path):
                with open(table_file_path + ".json") as f:
                    meta = json.load(f)
                column_names, column_types, nullable = parse_csv_meta(meta)
                data = pd.read_csv(
                    table_file_path, header=None, names=column_names, dtype=column_types, keep_default_na=False
                )
                data.to_csv(new_file_path, sep=sep, header=False, index=False)
            cursor.execute(
                """COPY "{}" FROM '{}' WITH DELIMITER '{}' NULL '';""".format(table_name, new_file_path, sep)
            )

        elif args.dbms != "hana":
            cursor.execute(load_command.format(table_name, table_file_path))

        else:
            try:
                cursor.execute(load_command.format(table_file_path, table_name))
                cursor.execute(f"MERGE DELTA OF {table_name};")
            except Exception as e:
                print("\nFailed to import table {}... with exception {}".format(table_name, e))
                pass
        end = time.time()
        print(f"({round(end - start, 1)} s)")

    cursor.close()
    if args.dbms == "umbra":
        connection.commit()
    connection.close()


def adapt_query(query):
    return query


def split_query(query):
    return [statement for statement in query.split(";") if statement.strip()]


def loop(thread_id, queries, query_id, start_time, successful_runs, timeout, is_warmup=False):
    connection, cursor = get_cursor()

    if is_warmup:
        if args.skip_warmup:
            return

        for q_id, query in enumerate(queries):
            try:
                cursor.execute(adapt_query(query))
                print("({})".format(q_id + 1), end="", flush=True)
            except Exception as e:
                print(e)
                print(adapt_query(query))
                raise e

        cursor.close()
        connection.close()
        return

    while True:
        if query_id == "shuffled":
            items = queries.copy()
            random.shuffle(items)
        else:
            items = [queries[query_id - 1]]
        if args.dbms == "hana":
            split_items = []
            for item in items:
                split_items += split_query(item)
            items = split_items
        item_start_time = time.time()
        for query in items:
            cursor.execute(adapt_query(query))
            cursor.fetchall()
            item_end_time = time.time()

        if (time.time() - start_time < timeout) or len(successful_runs) == 0:
            successful_runs.append((item_end_time - item_start_time) * 1000)
        else:
            break

    cursor.close()
    connection.close()


if args.benchmark == "TPCH":
    selected_benchmark_queries = tpch_queries
elif args.benchmark == "TPCDS":
    selected_benchmark_queries = tpcds_queries
elif args.benchmark == "SSB":
    selected_benchmark_queries = ssb_queries
elif args.benchmark == "JOB":
    selected_benchmark_queries = job_queries
elif args.benchmark == "all":
    selected_benchmark_queries = tpch_queries + tpcds_queries + ssb_queries + job_queries

if args.dbms == "monetdb":
    selected_benchmark_queries = [
        q.replace("!=", "<>").replace("SELECT MIN(chn.name) AS character,", 'SELECT MIN(chn.name) AS "character",')
        for q in selected_benchmark_queries
    ]

if not args.skip_data_loading:
    import_data()

if args.dbms in ["monetdb", "umbra", "greenplum", "hyrise-int"]:
    print("Warming up database (complete single-threaded run) due to initial persistence on disk: ", end="")
    sys.stdout.flush()
    loop(0, selected_benchmark_queries, "shuffled", time.time(), [], 3600, True)
    print(" done.")
    sys.stdout.flush()

if args.dbms == "hyrise-int":
    print("Performing dependency discovery", end="")
    sys.stdout.flush()
    connection, cursor = get_cursor()
    cursor.execute(
        """INSERT INTO meta_plugins values ('{}/lib/libhyriseDependencyDiscoveryPlugin.so');""".format(
            hyrise_server_path
        )
    )
    cursor.execute("INSERT INTO meta_exec values ('hyriseDependencyDiscoveryPlugin', 'DiscoverDependencies');")
    print(" done.")
    cursor.close()
    connection.close()

os.makedirs("db_comparison_results", exist_ok=True)

runtimes = {}
benchmark_queries = list(range(1, len(selected_benchmark_queries) + 1))

if args.clients > 1:
    benchmark_queries = ["shuffled"]
for query_id in benchmark_queries:
    query_name = "{} {:02}".format(args.benchmark, query_id) if query_id != "shuffled" else "shuffled"
    print("Benchmarking {}...".format(query_name), end="", flush=True)

    successful_runs = []
    start_time = time.time()

    timeout = args.time

    threads = []
    for thread_id in range(0, args.clients):
        threads.append(
            threading.Thread(
                target=loop,
                args=(thread_id, selected_benchmark_queries, query_id, start_time, successful_runs, timeout),
            )
        )
        threads[-1].start()

    while True:
        time_left = start_time + timeout - time.time()
        if time_left < 0:
            break
        print("\rBenchmarking {}... {:.0f} seconds left".format(query_name, time_left), end="")
        time.sleep(1)

    while True:
        joined_threads = 0
        for thread_id in range(0, args.clients):
            if not threads[thread_id].is_alive():
                # print(f't{thread_id} finished')
                joined_threads += 1

        if joined_threads == args.clients:
            break
        else:
            print(
                "\rBenchmarking {}... waiting for {} more clients to finish".format(
                    query_name, args.clients - joined_threads
                ),
                end="",
            )
            time.sleep(1)

    print("\r" + " " * 80, end="")
    print(
        "\r{}\t>>\t avg.: {:10.4f} ms\tmed.: {:10.4f} ms\tmin.: {:10.4f} ms\tmax.: {:10.4f} ms".format(
            query_name,
            sum(successful_runs) / len(successful_runs),
            statistics.median(successful_runs),
            min(successful_runs),
            max(successful_runs),
        )
    )

    runtimes[query_name] = successful_runs

rewrite_suffix = "__rewrites" if args.rewrites else ""
result_csv_filename = "db_comparison_results/database_comparison__{}__{}{}.csv".format(
    args.benchmark, args.dbms, rewrite_suffix
)
result_csv_exists = Path(result_csv_filename).exists()
with open(result_csv_filename, "a" if result_csv_exists else "w") as result_csv:
    if not result_csv_exists:
        result_csv.write("BENCHMARK,DATABASE_SYSTEM,CORES,CLIENTS,ITEM_NAME,RUNTIME_MS\n")
    for item_name, runs in runtimes.items():
        for run in runs:
            result_csv.write(
                "{},{},{},{},{},{}\n".format(args.benchmark, args.dbms, args.cores, args.clients, item_name, run)
            )
