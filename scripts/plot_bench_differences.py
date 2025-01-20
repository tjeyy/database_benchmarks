#!/usr/bin/env python3

import argparse as ap
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from palettable.cartocolors.qualitative import Safe_6


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("--data", "-d", type=str, default="./db_comparison_results")
    parser.add_argument("--output", "-o", type=str, default="./figures")
    return parser.parse_args()


def grep_throughput_change(old_result_file, new_result_file, clients, runtime):
    df_old = pd.read_csv(old_result_file)
    df_new = pd.read_csv(new_result_file)

    df_old = df_old[df_old.CLIENTS == clients]
    df_new = df_new[df_new.CLIENTS == clients]

    old_throughput = runtime / (df_old["RUNTIME_MS"].mean() / 1000)
    new_throughput = runtime / (df_new["RUNTIME_MS"].mean() / 1000)

    return new_throughput / old_throughput


def main(data_dir, output_dir):
    clients = 32
    runtime = 7200
    order = ["TPCH", "TPCDS", "SSB", "JOB"]
    changes = dict()

    for benchmark in order:
        common_path = f"database_comparison__{benchmark}__hana"
        old_path = os.path.join(data_dir, common_path + ".csv")
        new_path = os.path.join(data_dir, common_path + "__rewrites.csv")
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
    benchmark_count = len(order)
    colors = Safe_6.hex_colors[:benchmark_count]

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

    plt.savefig(os.path.join(output_dir, "benchmark_comparison.pdf"), dpi=300, bbox_inches="tight", pad_inches=0.01)
    plt.close()


if __name__ == "__main__":
    args = parse_args()
    main(args.data, args.output)
