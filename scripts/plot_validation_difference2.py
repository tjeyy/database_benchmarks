#!/usr/bin/env python3.11

import argparse as ap
import os
import re
from collections import defaultdict

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.ticker import FuncFormatter
from palettable.cartocolors.qualitative import Safe_6


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("commit", type=str)
    parser.add_argument("--data", "-d", type=str, default="./hyrise/cmake-build-release/benchmark_plugin_results")
    parser.add_argument("--output", "-o", type=str, default="./figures")
    return parser.parse_args()


def format_number(n):
    if n < 1 and n > 0:
        # return str(n)
        return ""
    return f"{int(n):,.0f}".replace(",", r"\thinspace")


def get_discovery_times(common_path):
    time_regexes = [
        re.compile(r"\d+(?=\ss)"),
        re.compile(r"\d+(?=\sms)"),
        re.compile(r"\d+(?=\sµs)"),
        re.compile(r"\d+(?=\sns)"),
    ]
    candidate_regex = re.compile(r"(?<=Checking )\w+(?= )")
    time_divs = list(reversed([1, 10**3, 10**6, 10**9]))

    candidate_times = defaultdict(list)

    with open(common_path) as f:
        for line in f:
            match = candidate_regex.search(line.strip())
            if not match:
                continue

            candidate_time = 0
            for regex, div in zip(time_regexes, time_divs):
                r = regex.search(line)
                if not r:
                    continue
                t = int(r.group(0))
                candidate_time += t * div
            if "rejected" in line:
                status = "invalid"
            elif "confirmed" in line:
                status = "valid"
            else:
                assert "skipped" in line
                status = "skipped"

            candidate_times[status].append(candidate_time)
    return candidate_times


def main(commit, data_dir, output_dir):
    benchmarks = {"TPCH": "TPC-H", "TPCDS": "TPC-DS", "StarSchema": "SSB", "JoinOrder": "JOB"}
    bens = ["TPC-H", "TPC-DS", "SSB", "JOB"]

    discovery_times_old = dict()
    discovery_times_new = dict()

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

    for benchmark, benchmark_title in benchmarks.items():
        sf_indicator = "" if benchmark_title == "JOB" else "_s10"
        common_path = os.path.join(data_dir, f"hyriseBenchmark{benchmark}_{commit}_st{sf_indicator}_plugin")
        old_path = os.path.join(data_dir, f"naive_validation_{benchmark_title.lower().replace('-', '')}.log")
        new_path = common_path + ".log"

        discovery_times_old[benchmark_title] = get_discovery_times(old_path)
        discovery_times_new[benchmark_title] = get_discovery_times(new_path)

    bar_width = 0.3
    margin = 0.02

    group_centers = np.arange(len(benchmarks))
    offsets = [-1, 1]

    for impl, disc_times, offset, color in zip(
        [r"na\"{i}ve", "optimized"], [discovery_times_old, discovery_times_new], offsets, Safe_6.hex_colors[:2]
    ):

        bar_positions = [
            p + offset * (0.5 * bar_width + margin) for p in group_centers
        ]
        t_sum = [
            (sum(disc_times[b]["valid"]) + sum(disc_times[b]["invalid"]) + sum(disc_times[b]["skipped"])) / 10**6
            for b in bens
        ]

        ax = plt.gca()
        ax.bar(bar_positions, t_sum, bar_width, color=color, label=f"{impl[0].upper()}{impl[1:]}")

        for y, x in zip(t_sum, bar_positions):
            label = str(round(y))
            ax.text(x, y * 1.2, label, ha="center", va="bottom", size=7 * 2)

    ax.set_yscale("symlog", linthresh=1)
    min_lim, max_lim = ax.get_ylim()
    ax.set_ylim(0, max_lim * 2)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: format_number(x)))

    plt.xticks(group_centers, bens, rotation=0)
    y_label = "Validation runtime [ms]"
    plt.ylabel(y_label, fontsize=8 * 2)
    plt.xlabel("Benchmark", fontsize=8 * 2)
    plt.legend(loc="best", fontsize=7 * 2, ncol=2, fancybox=False, framealpha=1.0)
    plt.grid(axis="x", visible=False)
    ax.tick_params(axis="both", which="major", labelsize=7 * 2)
    ax.tick_params(axis="both", which="minor", labelsize=7 * 2)
    fig = plt.gcf()

    column_width = 3.3374
    fig_width = column_width * 2
    fig_height = column_width * 0.475 * 2
    fig.set_size_inches(fig_width, fig_height)
    plt.tight_layout(pad=0)

    plt.savefig(os.path.join(output_dir, "validation_improvement_.pdf"), dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    args = parse_args()
    main(args.commit, args.data, args.output)
