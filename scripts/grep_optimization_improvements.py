#!/usr/bin/env python3


import argparse as ap
import json
import os
import re

import numpy as np


def to_s(n):
    return f"\\s{{{round(n / 10**9, 1)}}}"


def to_ms(n):
    ms = n / 10**6
    if ms < 1:
        return r"\ms{<1}"
    return f"\\ms{{{round(ms)}}}"


def perc(old, new):
    return f"\\perc{{{round(((new / old) - 1) * 100)}}}"


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("commit", type=str)
    parser.add_argument("--data", "-d", type=str, default="./hyrise/cmake-build-release/benchmark_plugin_results")
    return parser.parse_args()


def get_old_new_latency(old_path, new_path):
    with open(old_path) as old_file:
        old_data = json.load(old_file)

    with open(new_path) as new_file:
        new_data = json.load(new_file)

    if old_data["context"]["benchmark_mode"] != new_data["context"]["benchmark_mode"]:
        exit("Benchmark runs with different modes (ordered/shuffled) are not comparable")

    old_latencies = list()
    new_latencies = list()

    for old, new in zip(old_data["benchmarks"], new_data["benchmarks"]):
        # Create numpy arrays for old/new successful/unsuccessful runs from benchmark dictionary
        old_successful_durations = np.array([run["duration"] for run in old["successful_runs"]], dtype=np.float64)
        new_successful_durations = np.array([run["duration"] for run in new["successful_runs"]], dtype=np.float64)
        # np.mean() defaults to np.float64 for int input
        old_latencies.append(np.mean(old_successful_durations))
        new_latencies.append(np.mean(new_successful_durations))

    return sum(old_latencies), sum(new_latencies)


def get_discovery_stats(file_name):
    prefix = "Executed dependency discovery in "
    prefix_len = len(prefix)
    candidate_count = None
    valid_count = None
    candidate_regex = re.compile(r"Validated (?P<candidate>\d+) candidates \((?P<valid>\d+) valid")
    with open(file_name) as f:
        for line in f:
            if prefix in line:
                assert candidate_count is not None and valid_count is not None
                return [candidate_count, valid_count, line.strip()[prefix_len:]]
            match = candidate_regex.search(line)
            if match:
                candidate_count = match.group("candidate")
                valid_count = match.group("valid")
    raise AttributeError(f"Could not find discovery time in {file_name}")


def parse_duration(duration):
    time_regexes = [
        re.compile(r"\d+(?=\ss)"),
        re.compile(r"\d+(?=\sms)"),
        re.compile(r"\d+(?=\sµs)"),
        re.compile(r"\d+(?=\sns)"),
    ]
    time_divs = list(reversed([1, 10**3, 10**6, 10**9]))

    candidate_time = 0
    for regex, div in zip(time_regexes, time_divs):
        r = regex.search(duration)
        if not r:
            continue
        t = int(r.group(0))
        candidate_time += t * div

    return candidate_time


def main(commit, data_dir):
    benchmarks = ["TPCH", "TPCDS", "StarSchema", "JoinOrder"]
    configs = ["dgr", "jts", "jtp", "combined"]
    print("ALL OFF VS PLUGIN")
    for benchmark in benchmarks:
        print(benchmark)
        results = list()
        for opt in configs:
            common_path = os.path.join(data_dir, f"hyriseBenchmark{benchmark}_{commit}_st")
            if benchmark != "JoinOrder":
                common_path += "_s10"
            base_file = common_path + "_all_off.json"
            opt_extension = f"_{opt}" if opt != "combined" else ""
            opt_file = common_path + f"_plugin{opt_extension}.json"
            log_file = common_path + f"_plugin{opt_extension}.log"
            base_latency, opt_latency = get_old_new_latency(base_file, opt_file)

            stats = get_discovery_stats(log_file)

            results.append(
                [opt, to_s(base_latency), to_s(opt_latency - base_latency), perc(base_latency, opt_latency)]
                + stats[:1]
                + [to_ms(parse_duration(stats[2])), stats[-1]]
            )

        for i in range(len(results[0])):
            max_len = max(len(str(r[i])) for r in results)
            for r in results:
                r[i] = str(r[i]).rjust(max_len)
        for r in results:
            print(" & ".join(r))
        print()

    print("\nSCHEMA VS PLUGIN")
    for benchmark in benchmarks:
        print(benchmark)
        common_path = os.path.join(data_dir, f"hyriseBenchmark{benchmark}_{commit}_st")
        if benchmark != "JoinOrder":
            common_path += "_s10"
        base_file = common_path + "_schema.json"
        opt_file = common_path + "_schema_plugin.json"
        log_file = common_path + "_schema_plugin.log"
        base_latency, opt_latency = get_old_new_latency(base_file, opt_file)

        print(
            to_s(base_latency),
            to_s(opt_latency - base_latency),
            perc(base_latency, opt_latency),
            get_discovery_stats(log_file),
            sep=" & ",
        )


if __name__ == "__main__":
    args = parse_args()
    main(args.commit, args.data)
