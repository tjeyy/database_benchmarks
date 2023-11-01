#!/usr/bin/env python3.11

import math
import os
import re
from collections import defaultdict

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import rc
from palettable.cartocolors.qualitative import Antique_6, Bold_6, Pastel_6, Prism_6, Safe_6, Vivid_6


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

    benchmarks = ["TPCH", "TPCDS", "JoinOrder", "StarSchema"]
    type_regex = re.compile(r"(?<=Checking )\w+(?= )")
    time_regexes = [
        re.compile(r"\d+(?=\ss)"),
        re.compile(r"\d+(?=\sms)"),
        re.compile(r"\d+(?=\sµs)"),
        re.compile(r"\d+(?=\sns)"),
    ]
    time_divs = list(reversed([1, 10**3, 10**6, 10**9]))
    base_palette = Safe_6.hex_colors

    for benchmark in benchmarks:
        sf_indicator = "" if benchmark == "JoinOrder" else "_s10"
        common_path = f"hyriseBenchmark{benchmark}_{commit}_st{sf_indicator}_plugin.log"
        print(benchmark)

        candidate_times = defaultdict(list)

        with open(common_path) as f:
            for l in f:
                if not l.startswith("Checking"):
                    continue
                line = l.strip()
                candidate_type = type_regex.search(line).group()
                candidate_time = 0
                for regex, div in zip(time_regexes, time_divs):
                    r = regex.search(line)
                    if not r:
                        continue
                    t = int(r.group(0))
                    candidate_time += t * div
                candidate_time = candidate_time / 10**6  # get result in ms
                candidate_times[candidate_type].append(candidate_time)

        plot_data = defaultdict(list)
        benchmark_candidates = 0
        for candidate_type, validation_times in candidate_times.items():
            plot_data["time"] += validation_times
            candidate_count = len(validation_times)
            benchmark_candidates += candidate_count
            print("   ", candidate_type, sorted(validation_times))
            plot_data["type"] += [f"{candidate_type} ({candidate_count})"] * candidate_count

        print("   ", benchmark_candidates)

        unique_keys = sorted(set(plot_data["type"]))
        palette = defaultdict()
        for k in unique_keys:
            color_index = 0
            for c_id, dependency_type in enumerate(["FD", "IND", "OD", "UCC"]):
                if k.startswith(dependency_type):
                    color_index = c_id
                    break
            palette[k] = base_palette[c_id]

        ax = sns.boxplot(
            data=plot_data,
            x="type",
            y="time",
            color="white",
            order=unique_keys,
            boxprops={"fc": "w", "ec": "k"},
            whiskerprops={"c": "k"},
            flierprops={"mfc": "k", "mec": "k"},
            medianprops={"c": "k"},
            capprops={"c": "k"},
        )
        # iterate over boxes
        # for i,box in enumerate(ax.artists):
        #     box.set_edgecolor('black')
        #     box.set_facecolor('white')

        #     # iterate over whiskers and median lines
        #     for j in range(6*i,6*(i+1)):
        #          ax.lines[j].set_color('black')
        # plt.setp(ax.artists, edgecolor = 'k', facecolor='w')
        # plt.setp(ax.lines, color='k')

        ax = plt.gca()
        ax.set_yscale("symlog")
        ax.set_ylim(0, max(plot_data["time"]) * 1.5)

        plt.xlabel("Candidate type ($\\#$)", fontsize=8 * 2)
        plt.ylabel("Validation time [ms]", fontsize=8 * 2)
        ax.tick_params(axis="both", which="major", labelsize=6 * 2)
        ax.tick_params(axis="both", which="minor", labelsize=6 * 2)

        fig = plt.gcf()
        # fig.set_size_inches(18.5, 10.5)
        min_size = min(fig.get_size_inches())
        column_width = 3.3374
        fig_width = column_width * 0.475 * 2
        fig.set_size_inches(fig_width, fig_width)

        plt.tight_layout(pad=0)
        # print(os.path.join(output, f"{benchmark}_{file_indicator}_{config}_{metric}.{extension}"))
        plt.savefig(f"{benchmark}_validation_{commit}.pdf", dpi=300, bbox_inches="tight")
        plt.close()


if __name__ == "__main__":
    main()
