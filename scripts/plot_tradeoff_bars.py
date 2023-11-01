#!/usr/bin/env python3.11

import json
import math
import os
import re
from collections import defaultdict

import latex
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import rc
from matplotlib.ticker import FixedLocator, FuncFormatter, MaxNLocator
from palettable.cartocolors.qualitative import Antique_6, Bold_6, Pastel_6, Prism_6, Safe_6, Vivid_6


def format_number(n):
    if n < 1:
        return str(n)
    return str(int(n))

    for x in [1, 3, 5, 10]:
        if n == x:
            return str(int(n))
    return ""


def to_s(lst):
    return [x / 10**9 for x in lst]


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
        name = old["name"]
        # Create numpy arrays for old/new successful/unsuccessful runs from benchmark dictionary
        old_successful_durations = np.array([run["duration"] for run in old["successful_runs"]], dtype=np.float64)
        new_successful_durations = np.array([run["duration"] for run in new["successful_runs"]], dtype=np.float64)
        old_unsuccessful_durations = np.array([run["duration"] for run in old["unsuccessful_runs"]], dtype=np.float64)
        new_unsuccessful_durations = np.array([run["duration"] for run in new["unsuccessful_runs"]], dtype=np.float64)
        # np.mean() defaults to np.float64 for int input
        # if "TPCDS" in old_path and "95" in name:
        #    print("TPC-DS Q 95", to_s([np.mean(old_successful_durations), np.mean(new_successful_durations)]))
        #    # continue
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
    discovery_time_indicator = "Executed dependency discovery in "

    with open(common_path) as f:
        for l in f:
            if not l.startswith(discovery_time_indicator):
                continue
            line = l.strip()[len(discovery_time_indicator) :]
            candidate_time = 0
            for regex, div in zip(time_regexes, time_divs):
                r = regex.search(line)
                if not r:
                    continue
                t = int(r.group(0))
                candidate_time += t * div

            return candidate_time


def main():
    sns.set()
    sns.set_theme(style="whitegrid")
    # plt.style.use('seaborn-colorblind')
    # plt.rcParams['text.usetex'] = True
    # plt.rcParams["font.family"] = "serif"

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

    commit = "64fed166781996d29745cb99d662346e18ca8d74"
    commit = "b456ab78a170a9bb38958ccebb1293e12ade555b"
    commit = "9eb09b4feceb6eeb1c2bf8229f75ef7f6f8d001a"

    benchmarks = {"TPCH": "TPC-H", "TPCDS": "TPC-DS", "StarSchema": "SSB", "JoinOrder": "JOB"}
    all_scale_factors = range(1, 101)

    base_palette = Safe_6.hex_colors

    latencies_old = dict()
    latencies_new = dict()
    discovery_times = dict()

    for scale_factor in [10]:
        for benchmark, benchmark_title in benchmarks.items():
            sf_indicator = "" if benchmark_title == "JOB" else f"_s{scale_factor}"
            common_path = f"hyriseBenchmark{benchmark}_{commit}_st{sf_indicator}"

            old_path = common_path + ".json"
            new_path = common_path + "_plugin.json"

            latency_old, latency_new = get_latency_improvement(old_path, new_path)
            latencies_old[benchmark_title] = latency_old
            latencies_new[benchmark_title] = latency_new
            discovery_times[benchmark_title] = get_discovery_time(f"{common_path}_plugin.log")

    bar_width = 0.4
    epsilon = 0.015
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
    plt.savefig(f"benchmarks_combined_s10.svg", dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
