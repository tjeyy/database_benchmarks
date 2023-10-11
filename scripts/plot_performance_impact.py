#!/usr/bin/env python3.11

import os
import re
import json

import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import seaborn as sns
import latex
import math

from collections import defaultdict
from matplotlib import rc
from matplotlib.ticker import MaxNLocator, FixedLocator, FuncFormatter

import matplotlib as mpl


from palettable.cartocolors.qualitative import Antique_6, Bold_6, Pastel_6, Prism_6, Safe_6, Vivid_6

def format_number(n):
    if n < 1:
        return str(n)
    return str(int(n))

    for x in [1,3,5,10]:
        if n == x:
            return str(int(n))
    return ""


def to_s(lst):
    return [ x / 10**9 for x in lst]


def get_old_new_latencies(old_path, new_path):
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
        if "TPCDS" in old_path and "95" in name:
            print("TPC-DS Q 95", to_s([np.mean(old_successful_durations), np.mean(new_successful_durations)]))
            # continue
        old_latencies.append(np.mean(old_successful_durations))
        new_latencies.append(np.mean(new_successful_durations))

    return old_latencies, new_latencies

def main():
    sns.set()
    sns.set_theme(style="whitegrid")
    # plt.style.use('seaborn-colorblind')
    #plt.rcParams['text.usetex'] = True
    #plt.rcParams["font.family"] = "serif"

    mpl.use('pgf')

    plt.rcParams.update({
    "font.family": "serif",  # use serif/main font for text elements
    "text.usetex": True,     # use inline math for ticks
    "pgf.rcfonts": False,    # don't setup fonts from rc parameters
    "pgf.preamble":  r"""\usepackage{iftex}
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
  \fi"""
    })

    commit = "64fed166781996d29745cb99d662346e18ca8d74"
    commit = "b456ab78a170a9bb38958ccebb1293e12ade555b"
    commit = "6c461ce2cded091e5e58812a2a7106c0d9f73984"
    commit = "9eb09b4feceb6eeb1c2bf8229f75ef7f6f8d001a"

    benchmarks = ["TPCH", "TPCDS", "JoinOrder", "StarSchema"]

    base_palette = Safe_6.hex_colors

    color = base_palette[:1]

    for benchmark in benchmarks:
        common_path = f"hyriseBenchmark{benchmark}_{commit}_st"
        if benchmark != "JoinOrder":
            common_path = common_path + "_s10"
        old_path = common_path + ".json"
        new_path = common_path + "_plugin.json"
        old_latencies, new_latencies = get_old_new_latencies(old_path, new_path)

        dummy = [1 for _ in range(len(old_latencies))]
        values = pd.DataFrame(data={"old": to_s(old_latencies), "new": to_s(new_latencies), "d": dummy})

        max_value = to_s([max(max(old_latencies), max(new_latencies))])[0] * 1.05
        pl_data = [0, max_value]
        pl_data = pd.DataFrame(data={"x": pl_data, "y": pl_data, "d": [1,1]})

        sns.scatterplot(data=values, x="old", y="new", palette=color, hue="d", s=80, legend=False)
        #sns.lineplot(data=pl_data, x="x", y="y", palette=["lightgrey"], hue="d", style="d", sizes=(0.2,0.2), legend=False)

        ax = plt.gca()

        plt.ylabel('Latency w/ optimizations [s]', fontsize=8*2)
        plt.xlabel('Base latency [s]', fontsize=8*2)
        ax.tick_params(axis='both', which='major', labelsize=7*2)
        ax.tick_params(axis='both', which='minor', labelsize=7*2)


        ax.set_yscale('log')
        ax.set_xscale('log')


        significant_improvement = 0
        significant_degradation = 0
        significance_level = 0.05

        for old, new in zip(old_latencies, new_latencies):
            ratio = new / old
            if ratio <= 1 - significance_level:
                significant_improvement = significant_improvement + 1
                continue
            if ratio >= 1 + significance_level:
                significant_degradation = significant_degradation + 1

        print(benchmark, round((1 - sum(new_latencies) / sum(old_latencies)) * 100), "% improvement,", significant_improvement, "better,", significant_degradation, "worse")

        #if benchmark == "TPCDS":
        #    max_value = 3.99


        min_lim = min(ax.get_ylim()[0], ax.get_xlim()[0])
        max_lim = max(ax.get_ylim()[1], ax.get_xlim()[1])
        if benchmark == "StarSchema":
            max_lim = 6

        possible_ticks_below_one = [10**(-exp) for exp in reversed(range(1, 4))]
        possible_ticks_above_one = [1, 3, 5, 10]
        ticks = list()
        for tick in possible_ticks_below_one:
            if tick >= min_lim:
                ticks.append(tick)
        for tick in possible_ticks_above_one:
            if tick <= max_lim:
                ticks.append(tick)
        #ticks += psossible_ticks_above_one
        print(min_lim, max_lim, ticks)
        ax.set_ylim(min_lim, max_lim)
        ax.set_xlim(min_lim, max_lim)

        pl_data = [min_lim, max_lim]
        pl_data = pd.DataFrame(data={"x": pl_data, "y": pl_data, "d": [1,1]})

        sns.lineplot(data=pl_data, x="x", y="y", palette=["lightgrey"], hue="d", style="d", sizes=(0.2,0.2), legend=False)

        #ax.set_ylim(0, max_value)
        #ax.set_xlim(0, max_value)
        #ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        #ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.yaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: format_number(x)))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: format_number(x)))
        plt.grid(dashes=(3,5))

        fig = plt.gcf()
        r"""
        \usepackage{layouts}
        \printinunitsof{in}\prntlen{\columnwidth}
        """
        column_width = 3.3374
        fig_width = column_width * 0.475 * 2
        fig.set_size_inches(fig_width, fig_width)
        plt.tight_layout(pad=0)
        # ax.set_box_aspect(1)


        # print(os.path.join(output, f"{benchmark}_{file_indicator}_{config}_{metric}.{extension}"))
        # plt.savefig(f"{benchmark}_log_{commit}.pdf", dpi=300, bbox_inches="tight")
        plt.savefig(f"{benchmark}_log.pdf", dpi=300, bbox_inches="tight")
        plt.close()

if __name__ == '__main__':
    main()
