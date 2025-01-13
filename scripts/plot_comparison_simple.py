#!/usr/bin/env python3

import argparse as ap
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from palettable.cartocolors.qualitative import Safe_10


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("--data", "-d", type=str, default="./db_comparison_results")
    parser.add_argument("--output", "-o", type=str, default="./figures")
    parser.add_argument("--metric", "-m", type=str, default="runtime", choices=["throughput", "runtime"])
    return parser.parse_args()


def grep_throughput_change(old_result_file, new_result_file, clients, runtime):
    if not (os.path.isfile(old_result_file) and os.path.isfile(new_result_file)):
        print("-")
        return 1
    df_old = pd.read_csv(old_result_file)
    df_new = pd.read_csv(new_result_file)

    df_old = df_old[df_old.CLIENTS == clients]
    df_new = df_new[df_new.CLIENTS == clients]

    print(
        f'{round((1 - (df_new["RUNTIME_MS"].median() / 1000) / (df_old["RUNTIME_MS"].median() / 1000)) * 100, 2)}%', end=" "
    )

    print(f'({round(df_old["RUNTIME_MS"].median() / 1000, 2)} / {round(df_new["RUNTIME_MS"].median() / 1000, 2)})')

    old_throughput = runtime / (df_old["RUNTIME_MS"].median() / 1000)
    new_throughput = runtime / (df_new["RUNTIME_MS"].median() / 1000)

    return new_throughput / old_throughput


def grep_runtime_change(old_result_file, new_result_file, clients, runtime):
    if not (os.path.isfile(old_result_file) and os.path.isfile(new_result_file)):
        print("-")
        return 1
    df_old = pd.read_csv(old_result_file)
    df_new = pd.read_csv(new_result_file)

    df_old = df_old[df_old.CLIENTS == clients]
    df_new = df_new[df_new.CLIENTS == clients]

    print(
        f'{round((1 - (df_new["RUNTIME_MS"].median() / 1000) / (df_old["RUNTIME_MS"].median() / 1000)) * 100, 2)}%', end=" "
    )

    print(f'({round(df_old["RUNTIME_MS"].median() / 1000, 2)} / {round(df_new["RUNTIME_MS"].median() / 1000, 2)})')

    old_runtime = df_old["RUNTIME_MS"].median()
    new_runtime = df_new["RUNTIME_MS"].median()

    return new_runtime / old_runtime


def main(data_dir, output_dir, metric):
    clients = 32
    runtime = 7200
    order = list(reversed(["hyrise-int", "hyrise", "umbra", "hana", "monetdb", "greenplum"]))
    changes = dict()
    HANA_NAME = "SAP HANA"

    for benchmark in ["all"]:  # , "TPCH", "TPCDS", "SSB", "JOB"]:
        print(f"\n\n{benchmark}")

        print("LATENCY")
        for dbms in order:
            print(dbms, end=": ")
            common_path = f"database_comparison__{benchmark}__{dbms}"
            old_path = os.path.join(data_dir, common_path + ".csv")
            new_path = os.path.join(data_dir, common_path + "__rewrites.csv")
            if dbms == "hyrise-int":
                new_path = old_path
                old_path = os.path.join(data_dir, common_path[: -len("-int")] + ".csv")
            method = grep_throughput_change if metric == "throughput" else grep_runtime_change
            changes[dbms] = method(old_path, new_path, clients, runtime)
        if all([v == 1 for v in changes.values()]):
            continue
        changes = {k: abs((v - 1) * 100) for k, v in changes.items()}

        print(metric.upper())
        max_len = max([len(db) for db in order])
        for dbms in order:
            print(f"{dbms.rjust(max_len)}: {round(changes[dbms], 2)}%")

        names = {
            "hyrise-int": "Hyrise\n(optimizer)",
            "hyrise": "Hyrise",
            "monetdb": "MonetDB",
            "umbra": "Umbra",
            "hana": HANA_NAME,
            "greenplum": "Greenplum",
            "greenplum-rows": "Greenplum\n(row)",
        }

        sns.set_theme(style="white")
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
        colors = [c for c in Safe_10.hex_colors[:db_count]] + [Safe_10.hex_colors[db_count - 1]]

        for d, color, pos, h in zip(order, colors, group_centers, hatches):
            plt.bar(
                [pos], [changes[d]], bar_width, color=color, hatch=h, edgecolor="white", linewidth=0.0, linestyle=""
            )

        plt.xticks(group_centers, [names[d] for d in order], rotation=0)
        ax = plt.gca()
        plt.ylabel(f"Average {metric}\nimprovement [\\%]", fontsize=8 * 2)
        plt.xlabel("System", fontsize=8 * 2)
        ax.tick_params(axis="both", which="major", labelsize=7 * 2, width=1, length=6, left=True, bottom=True)

        plt.grid(axis="y", visible=True)
        fig = plt.gcf()
        column_width = 3.3374
        fig_width = column_width * 2
        fig_height = column_width * 0.475 * 2
        fig.set_size_inches(fig_width, fig_height)
        plt.tight_layout(pad=0)

        plt.savefig(
            os.path.join(output_dir, f"systems_comparison_simple_{benchmark.lower()}_{metric}.pdf"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()


if __name__ == "__main__":
    args = parse_args()
    main(args.data, args.output, args.metric)
