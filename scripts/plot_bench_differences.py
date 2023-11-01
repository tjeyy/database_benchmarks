#!/usr/bin/env python3

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


def grep_throughput_change(old_result_file, new_result_file, clients, runtime):
    # if not (os.path.isfile(old_result_file) and os.path.isfile(new_result_file)):
    #    return 1
    df_old = pd.read_csv(old_result_file)
    df_new = pd.read_csv(new_result_file)

    df_old = df_old[df_old.CLIENTS == clients]
    df_new = df_new[df_new.CLIENTS == clients]

    old_throughput = runtime / (df_old["RUNTIME_MS"].mean() / 1000)
    new_throughput = runtime / (df_new["RUNTIME_MS"].mean() / 1000)

    return new_throughput / old_throughput


def main():
    clients = 32
    runtime = 3600

    order = ["TPCH", "TPCDS", "SSB", "JOB"]

    changes = dict()

    for benchmark in order:
        common_path = f"db_comparison_results/database_comparison__{benchmark}__hana"
        old_path = common_path + ".csv"
        new_path = common_path + "__rewrites.csv"
        changes[benchmark] = grep_throughput_change(old_path, new_path, clients, runtime)

    changes = {k: (v - 1) * 100 for k, v in changes.items()}

    max_len = max([len(db) for db in order])
    for benchmark in order:
        print(f"{benchmark.rjust(max_len)}: {round(changes[benchmark], 2)}%")

    names = {"TPCH": "TPC-H", "TPCDS": "TPC-DS", "SSB": "SSB", "JOB": "JOB"}

    sns.set()
    sns.set_theme(style="whitegrid")
    plt.rcParams["font.family"] = "serif"

    bar_width = 0.4

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

    group_centers = np.arange(len(order))
    colors = [c for c in Safe_6.hex_colors[: len(order)]]

    for d, color, pos in zip(order, colors, group_centers):
        plt.bar([pos], [changes[d]], bar_width, color=color)

    plt.xticks(group_centers, [names[d] for d in order], rotation=0)
    ax = plt.gca()
    plt.ylabel(r"Throughput improvement [\%]", fontsize=8 * 2)
    plt.xlabel("Benchmark", fontsize=8 * 2)
    ax.tick_params(axis="both", which="major", labelsize=7 * 2)
    ax.tick_params(axis="both", which="minor", labelsize=7 * 2)
    plt.grid(axis="x", visible=False)
    fig = plt.gcf()
    column_width = 3.3374
    fig_width = column_width * 2
    fig_height = column_width * 0.475 * 2
    plt.tight_layout(pad=0)
    fig.set_size_inches(fig_width, fig_height)

    plt.savefig(f"figures/benchmark_comparison.pdf", dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
