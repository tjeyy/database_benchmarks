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
    if not (os.path.isfile(old_result_file) and os.path.isfile(new_result_file)):
        return 1
    df_old = pd.read_csv(old_result_file)
    df_new = pd.read_csv(new_result_file)

    df_old = df_old[df_old.CLIENTS == clients]
    df_new = df_new[df_new.CLIENTS == clients]

    old_throughput = runtime / (df_old["RUNTIME_MS"].mean() / 1000)
    new_throughput = runtime / (df_new["RUNTIME_MS"].mean() / 1000)

    return new_throughput / old_throughput


def main():
    clients = 18
    runtime = 7200

    order = list(reversed(["hyrise-int", "hyrise", "hana", "umbra", "monetdb", "greenplum"]))

    changes = dict()

    for dbms in order[:-1]:
        common_path = f"db_comparison_results/database_comparison__all__{dbms}"
        old_path = common_path + ".csv"
        new_path = common_path + "__rewrites.csv"
        changes[dbms] = grep_throughput_change(old_path, new_path, clients, runtime)
    changes["hyrise-int"] = grep_throughput_change(
        "db_comparison_results/database_comparison__all__hyrise.csv",
        "db_comparison_results/database_comparison__all__hyrise-int.csv",
        clients,
        runtime,
    )

    changes = {k: (v - 1) * 100 for k, v in changes.items()}

    max_len = max([len(db) for db in order])
    for dbms in order:
        print(f"{dbms.rjust(max_len)}: {round(changes[dbms], 2)}%")

    names = {
        "hyrise-int": "Hyrise\n(internal)",
        "hyrise": "Hyrise",
        "monetdb": "MonetDB",
        "umbra": "Umbra",
        "hana": "System X",
        "greenplum": "Greenplum",
    }

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
    db_count = len(order) - 1
    hatches = [None] * db_count + ["/"]
    colors = [c for c in Safe_6.hex_colors[:db_count]] + [Safe_6.hex_colors[db_count - 1]]

    for d, color, pos, h in zip(order, colors, group_centers, hatches):
        plt.bar([pos], [changes[d]], bar_width, color=color, hatch=h)

    plt.xticks(group_centers, [names[d] for d in order], rotation=0)
    ax = plt.gca()
    plt.ylabel(r"Throughput improvement [\%]", fontsize=8 * 2)
    plt.xlabel("System", fontsize=8 * 2)
    ax.tick_params(axis="both", which="major", labelsize=7 * 2)
    ax.tick_params(axis="both", which="minor", labelsize=7 * 2)
    plt.grid(axis="x", visible=False)
    fig = plt.gcf()
    column_width = 3.3374
    fig_width = column_width * 2
    fig_height = column_width * 0.475 * 2
    plt.tight_layout(pad=0)
    fig.set_size_inches(fig_width, fig_height)

    plt.savefig(f"figures/systems_comparison.pdf", dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
