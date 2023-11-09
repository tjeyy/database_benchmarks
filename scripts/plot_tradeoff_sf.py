#!/usr/bin/env python3.11

import argparse as ap
import json
import os
import re
from collections import defaultdict

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from palettable.cartocolors.qualitative import Safe_6


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("commit", type=str)
    parser.add_argument("--data", "-d", type=str, default="./hyrise/cmake-build-release/benchmark_plugin_results")
    parser.add_argument("--output", "-o", type=str, default="./figures")
    return parser.parse_args()


def format_number(n):
    if n < 1:
        return str(n)
    return str(int(n))

    for x in [1, 3, 5, 10]:
        if n == x:
            return str(int(n))
    return ""


def to_s(v):
    def val_to_s(x):
        return x / 10**9

    if type(v) != list:
        return val_to_s(v)
    return [val_to_s(i) for i in v]


def get_latencies(old_path, new_path):
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
        for line in f:
            if not line.startswith(discovery_time_indicator):
                continue
            candidate_time = 0
            for regex, div in zip(time_regexes, time_divs):
                r = regex.search(line)
                if not r:
                    continue
                t = int(r.group(0))
                candidate_time += t * div

            return candidate_time


def main(commit, data_dir, output_dir):
    benchmarks = {"TPCH": "TPC-H", "TPCDS": "TPC-DS", "StarSchema": "SSB"}
    all_scale_factors = range(1, 101)

    base_palette = Safe_6.hex_colors

    latency_improvements = defaultdict(list)
    discovery_times = defaultdict(list)
    scale_factors = list()
    latency_improvements_relative = defaultdict(list)
    discovery_times_relative = defaultdict(list)

    for scale_factor in all_scale_factors:
        sf_indicator = "" if scale_factor == 10 else f"_s{scale_factor}"
        sf_indicator = f"_s{scale_factor}"
        if not os.path.isfile(os.path.join(data_dir, f"hyriseBenchmarkTPCH_{commit}_st{sf_indicator}.log")):
            continue

        scale_factors.append(scale_factor)

        for benchmark, benchmark_title in benchmarks.items():
            common_path = os.path.join(data_dir, f"hyriseBenchmark{benchmark}_{commit}_st{sf_indicator}")
            old_path = common_path + ".json"
            new_path = common_path + "_plugin.json"

            old_latency, new_latency = get_latencies(old_path, new_path)
            discovery_time = get_discovery_time(f"{common_path}_plugin.log")

            latency_improvements[benchmark_title].append(to_s(old_latency - new_latency))
            discovery_times[benchmark_title].append(to_s(discovery_time))

            latency_improvements_relative[benchmark_title].append((old_latency - new_latency) * 100 / old_latency)
            discovery_times_relative[benchmark_title].append(discovery_time * 100 / old_latency)

    print(scale_factors)

    for measurement_type, lat_improvements, disc_times in zip(
        ["abs", "rel"],
        [latency_improvements, latency_improvements_relative],
        [discovery_times, discovery_times_relative],
    ):
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

        x_axis_sf = list()
        y_axis_time = list()
        indicator_measurement = list()
        indicator_benchmark = list()

        for benchmark, latency_improvement in lat_improvements.items():
            discovery_time = disc_times[benchmark]
            assert len(discovery_time) == len(latency_improvement) and len(discovery_time) == len(scale_factors)

            x_axis_sf += scale_factors * 2

            y_axis_time += latency_improvement
            y_axis_time += discovery_time

            indicator_measurement += ["Latency Improvement"] * len(latency_improvement)
            indicator_measurement += ["Discovery Time"] * len(discovery_time)

            indicator_benchmark += [benchmark] * len(scale_factors) * 2

        assert (
            len(x_axis_sf) == len(y_axis_time)
            and len(x_axis_sf) == len(indicator_measurement)
            and len(x_axis_sf) == len(indicator_benchmark)
        )

        values = pd.DataFrame(
            data={
                "x": x_axis_sf,
                "y": y_axis_time,
                "Measurement": indicator_measurement,
                "Benchmark": indicator_benchmark,
            }
        )

        dashes = {"Discovery Time": (3, 3), "Latency Improvement": ""}
        markers = ["^", "X", "s", "D", ".", "o"]

        sns.lineplot(
            data=values,
            x="x",
            y="y",
            style="Measurement",
            markers=markers[:2],
            markersize=8,
            hue="Benchmark",
            dashes=dashes,
            palette=base_palette[: len(benchmarks)],
        )

        ax = plt.gca()

        y_label = "Runtime [s]" if measurement_type == "abs" else "Share of Runtime [%]"
        plt.ylabel(y_label, fontsize=8 * 2)
        plt.xlabel("Scale factor", fontsize=8 * 2)
        plt.legend(fontsize=6 * 2, fancybox=False, framealpha=1.0)
        ax.tick_params(axis="both", which="major", labelsize=7 * 2)
        ax.tick_params(axis="both", which="minor", labelsize=7 * 2)

        plt.ylim((plt.ylim()[0], 110))
        fig = plt.gcf()

        column_width = 3.3374
        fig_width = column_width * 2
        fig_height = column_width * 0.475 * 2
        fig.set_size_inches(fig_width, fig_height)
        plt.tight_layout(pad=0)

        plt.savefig(
            os.path.join(output_dir, f"benchmarks_combined_sf_{measurement_type}.pdf"), dpi=300, bbox_inches="tight"
        )
        plt.close()


if __name__ == "__main__":
    args = parse_args()
    main(args.commit, args.data, args.output)
