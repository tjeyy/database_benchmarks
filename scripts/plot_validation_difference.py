#!/usr/bin/env python3.11

import argparse as ap
import os
import re
from collections import defaultdict

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.ticker import FixedLocator, FuncFormatter
from palettable.cartocolors.qualitative import Safe_6


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("commit", type=str)
    parser.add_argument("--data", "-d", type=str, default="./hyrise/cmake-build-release/benchmark_plugin_results")
    parser.add_argument("--output", "-o", type=str, default="./figures")
    parser.add_argument("--scale", "-s", type=str, default="log", choices=["linear", "log", "symlog"])
    return parser.parse_args()


def format_number(n):
    return f"{int(n):,.0f}".replace(",", r"\thinspace") if n % 1 == 0 else str(n)


def get_discovery_times(common_path):
    time_regexes = [
        re.compile(r"\d+(?=\ss)"),
        re.compile(r"\d+(?=\sms)"),
        re.compile(r"\d+(?=\sµs)"),
        re.compile(r"\d+(?=\sns)"),
    ]
    candidate_regex = re.compile(r"(?<=Checking )(?P<candidate>[^\[]+) \[.+ in ")
    time_divs = list(reversed([1, 10**3, 10**6, 10**9]))

    candidate_times = defaultdict(list)
    time_per_candidate = dict()

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
            ts_start = match.end()
            time_per_candidate[match.group("candidate")] = (status, candidate_time, line.strip()[ts_start:-1])

    return candidate_times, time_per_candidate


def main(commit, data_dir, output_dir, scale):
    benchmarks = {"TPCH": "TPC-H", "TPCDS": "TPC-DS", "StarSchema": "SSB", "JoinOrder": "JOB"}
    bens = ["TPC-H", "TPC-DS", "SSB", "JOB"]

    discovery_times_old = dict()
    discovery_times_new = dict()

    candidate_times_old = dict()
    candidate_times_new = dict()

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
        old_path = os.path.join(data_dir, f"hyriseBenchmark{benchmark}_st{sf_indicator}_plugin_naive.log")
        new_path = os.path.join(data_dir, f"hyriseBenchmark{benchmark}_{commit}_st{sf_indicator}_plugin.log")

        discovery_times_old[benchmark_title], candidate_times_old[benchmark_title] = get_discovery_times(old_path)
        discovery_times_new[benchmark_title], candidate_times_new[benchmark_title] = get_discovery_times(new_path)

    bar_width = 0.3
    margin = 0.02

    group_centers = np.arange(len(benchmarks))
    offsets = [-1, 1]

    for impl, disc_times, offset, color in zip(
        [r"na\"{i}ve", "optimized"], [discovery_times_old, discovery_times_new], offsets, Safe_6.hex_colors[:2]
    ):

        bar_positions = [p + offset * (0.5 * bar_width + margin) for p in group_centers]
        t_sum = [
            (sum(disc_times[b]["valid"]) + sum(disc_times[b]["invalid"]) + sum(disc_times[b]["skipped"])) / 10**6
            for b in bens
        ]

        print(impl.upper())
        res = [bens.copy(), [str(round(x, 2)) for x in t_sum]]
        for i in range(len(bens)):
            max_len = max([len(r[i]) for r in res])
            for r in res:
                r[i] = r[i].rjust(max_len)
        for r in res:
            print("  ".join(r))
        print()

        ax = plt.gca()
        ax.bar(bar_positions, t_sum, bar_width, color=color, label=f"{impl[0].upper()}{impl[1:]}", edgecolor="none")

        for y, x in zip(t_sum, bar_positions):
            label = str(round(y, 1))
            y = y * 1.2 if scale != "linear" else y + 100
            ax.text(x, y, label, ha="center", va="bottom", size=7 * 2)

    print("SPEEDUP")
    for benchmark in bens:
        discovery_time_old = (
            sum(discovery_times_old[benchmark]["valid"])
            + sum(discovery_times_old[benchmark]["invalid"])
            + sum(discovery_times_old[benchmark]["skipped"])
        )
        discovery_time_new = (
            sum(discovery_times_new[benchmark]["valid"])
            + sum(discovery_times_new[benchmark]["invalid"])
            + sum(discovery_times_new[benchmark]["skipped"])
        )
        print(f"{benchmark.rjust(max([len(b) for b in bens]))}: {discovery_time_old / discovery_time_new}")

    for benchmark in bens:
        print(f"\nCOMPARISON {benchmark}")
        for candidate in sorted(candidate_times_old[benchmark].keys()):
            status_old, time_old, time_readable_old = candidate_times_old[benchmark][candidate]
            status_new, time_new, time_readable_new = candidate_times_new[benchmark][candidate]
            print(
                candidate,
                status_old,
                status_new,
                f"{round(time_new * 100 / time_old, 2)}%",
                time_readable_old,
                time_readable_new,
            )

    if scale == "symlog":
        ax.set_yscale("symlog", linthresh=1)
    else:
        ax.set_yscale(scale)
    max_lim = ax.get_ylim()[1]
    max_lim = max_lim * 2.5 if scale != "linear" else max_lim * 1.05
    min_lim = 0 if scale != "log" else 1
    ax.set_ylim(min_lim, max_lim)

    possible_minor_ticks = []
    if scale != "linear":
        factors = [1, 10, 100, 1000]
        if scale == "symlog":
            factors = [1 / 10] + factors
        for factor in factors:
            possible_minor_ticks += [n * factor for n in range(1, 10)]
    minor_ticks = list()
    for tick in possible_minor_ticks:
        if tick >= min_lim and tick <= max_lim:
            minor_ticks.append(tick)

    plt.xticks(group_centers, bens, rotation=0)
    y_label = "Validation runtime [ms]"
    plt.ylabel(y_label, fontsize=8 * 2)
    plt.xlabel("Benchmark", fontsize=8 * 2)
    plt.legend(loc="best", fontsize=7 * 2, ncol=2, fancybox=False, framealpha=1.0, edgecolor="black")
    plt.grid(axis="x", visible=False)
    fig = plt.gcf()

    ax.tick_params(axis="both", which="major", labelsize=7 * 2, width=1, length=6, left=True, color="black")
    ax.tick_params(axis="y", which="minor", width=0.5, length=4, left=True, color="black")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: format_number(x)))
    ax.yaxis.set_minor_locator(FixedLocator(minor_ticks))
    ax.spines["top"].set_color("black")
    ax.spines["bottom"].set_color("black")
    ax.spines["left"].set_color("black")
    ax.spines["right"].set_color("black")

    column_width = 3.3374
    fig_width = column_width * 2
    fig_height = column_width * 0.475 * 2
    fig.set_size_inches(fig_width, fig_height)
    plt.tight_layout(pad=0)

    plt.savefig(os.path.join(output_dir, f"validation_improvement_{scale}.pdf"), dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    args = parse_args()
    main(args.commit, args.data, args.output, args.scale)
