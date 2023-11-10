#!/usr/bin/env python3.11

import argparse as ap
import json
import os
import re

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("commit", type=str)
    parser.add_argument("--data", "-d", type=str, default="./hyrise/cmake-build-release/benchmark_plugin_results")
    parser.add_argument("--output", "-o", type=str, default="./figures")
    return parser.parse_args()


def get_latency_improvement(old_path, new_path):
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


def get_discovery_time(common_path):
    time_regexes = [
        re.compile(r"\d+(?=\ss)"),
        re.compile(r"\d+(?=\sms)"),
        re.compile(r"\d+(?=\sµs)"),
        re.compile(r"\d+(?=\sns)"),
    ]
    time_divs = list(reversed([1, 10**3, 10**6, 10**9]))
    generation_time_indicator = "Generated "
    validation_time_indicator = "Validated "
    discovery_time = 0

    with open(common_path) as f:
        for line in f:
            if not (line.startswith(generation_time_indicator) or line.startswith(validation_time_indicator)):
                continue
            for regex, div in zip(time_regexes, time_divs):
                r = regex.search(line)
                if not r:
                    continue
                t = int(r.group(0))
                discovery_time += t * div

    return discovery_time


def main(commit, data_dir, output_dir):
    sns.set()
    sns.set_theme(style="whitegrid")

    mpl.use("pgf")

    plt.rcParams.update(
        {
            "font.family": "serif",  # use serif/main font for text elements
            "text.usetex": True,  # use inline math for ticks
            "pgf.rcfonts": False,  # don't setup fonts from rc parameters
            "pgf.preamble": r"""\usepackage{iftex}
  \ifxetex
    \usepackage[libertine]{newtxmath}
    \usepackage[tt=false]{libertine}
    \setmonofont[StylisticSet=3]{inconsolata}
  \else
    \ifluatex
      \usepackage[libertine]{newtxmath}
      \usepackage[tt=false]{libertine}
      \setmonofont[StylisticSet=3]{inconsolata}
    \else
       \usepackage[tt=false, type1=true]{libertine}
       \usepackage[varqu]{zi4}
       \usepackage[libertine]{newtxmath}
    \fi
  \fi""",
        }
    )

    benchmarks = {"TPCH": "TPC-H", "TPCDS": "TPC-DS", "StarSchema": "SSB", "JoinOrder": "JOB"}

    latencies_old = dict()
    latencies_new = dict()
    discovery_times = dict()

    for scale_factor in [10]:
        for benchmark, benchmark_title in benchmarks.items():
            sf_indicator = "" if benchmark_title == "JOB" else f"_s{scale_factor}"
            common_path = f"hyriseBenchmark{benchmark}_{commit}_st{sf_indicator}"

            old_path = os.path.join(data_dir, common_path + "_all_off.json")
            new_path = os.path.join(data_dir, common_path + "_plugin.json")

            latency_old, latency_new = get_latency_improvement(old_path, new_path)
            latencies_old[benchmark_title] = latency_old
            latencies_new[benchmark_title] = latency_new
            discovery_times[benchmark_title] = get_discovery_time(f"{common_path}_plugin.log")

    bar_width = 0.4
    margin = 0.00

    group_centers = np.arange(len(benchmarks))
    offsets = [-0.5, 0.5]
    ax = plt.gca()

    bens = ["JOB", "SSB", "TPC-DS", "TPC-H"]

    bar_positions = [p + offsets[0] * (bar_width + margin) for p in group_centers]
    baselines = [latencies_old[b] / 10**9 for b in bens]
    ax.bar(bar_positions, baselines, bar_width, color="#848787", label="Baseline", linewidth=0)

    bar_positions = [p + offsets[1] * (bar_width + margin) for p in group_centers]
    overheads = [(latencies_new[b] + discovery_times[b]) / 10**9 for b in bens]
    ax.bar(bar_positions, overheads, bar_width, color="#e8723c", label="Overhead (once)", linewidth=0)

    optimized = [latencies_new[b] / 10**9 for b in bens]
    ax.bar(bar_positions, optimized, bar_width, color="#57a3d5", label="Optimized", linewidth=0)

    plt.xticks(group_centers, bens, rotation=0)
    plt.grid(which="major", axis="x", visible=False)
    ax.tick_params(axis="both", which="major", labelsize=7 * 2)
    ax.tick_params(axis="both", which="minor", labelsize=7 * 2)
    plt.ylabel("Runtime [s]", fontsize=8 * 2)
    # plt.xlabel('Benchmark', fontsize=8*2)

    handles, labels = plt.gca().get_legend_handles_labels()
    order = [0, 2, 1]

    plt.legend(
        [handles[idx] for idx in order],
        [labels[idx] for idx in order],
        ncols=3,
        bbox_to_anchor=[0.5, 1.15],
        loc="upper center",
        frameon=False,
    )

    column_width = 3.3374
    fig_width = column_width * 2 * (2 / 3)
    fig_height = column_width
    fig = plt.gcf()
    fig.set_size_inches(fig_width, fig_height)
    plt.tight_layout(pad=0)
    plt.savefig(os.path.join(output_dir, "benchmarks_combined_s10.svg"), dpi=300, bbox_inches="tight")
    plt.savefig(os.path.join(output_dir, "benchmarks_combined_s10.pdf"), dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    args = parse_args()
    main(args.commit, args.data, args.output)
