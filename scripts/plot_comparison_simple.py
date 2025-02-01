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


def grep_throughput(result_file, clients, runtime):
    if not (os.path.isfile(result_file)):
        print("-")
        return np.nan

    df = pd.read_csv(result_file)

    if "hana" in result_file:
        df = df[df.RUNTIME_MS > 1000]

    return runtime / (df[df.CLIENTS == clients].RUNTIME_MS.median() / 1000)


def grep_runtime(result_file, clients, runtime):
    if not (os.path.isfile(result_file)):
        return np.nan

    df = pd.read_csv(result_file)

    if "hana" in result_file:
        df = df[df.RUNTIME_MS > 1000]

    return df[df.CLIENTS == clients].RUNTIME_MS.median()


def main(data_dir, output_dir, metric):
    clients = 32
    runtime = 7200
    order = list(reversed(["hyrise-int", "hyrise", "hana", "umbra", "monetdb", "greenplum"]))[1:-1]
    changes = dict()
    HANA_NAME = "SAP HANA"

    for benchmark in ["all"]:  # , "TPCH", "TPCDS", "SSB", "JOB"]:
        print(f"\n\n{benchmark}")

        for dbms in order:
            print(dbms, end=": ")
            common_path = f"database_comparison__{benchmark}__{dbms}"
            base_path = os.path.join(data_dir, common_path + ".csv")
            keys_path = old_path = os.path.join(data_dir, common_path + "__keys.csv")
            rewrites_path = os.path.join(data_dir, common_path + f"__rewrites.csv")
            rewrites_keys_path = os.path.join(data_dir, common_path + f"__rewrites__keys.csv")
            if dbms == "hyrise-int":
                base_path = os.path.join(data_dir, common_path[: -len("-int")] + ".csv")
                keys_path = old_path = os.path.join(data_dir, common_path[: -len("-int")] + "__keys.csv")
                rewrites_path = os.path.join(data_dir, common_path + ".csv")
                rewrites_keys_path = rewrites_path

            method = grep_throughput if metric == "throughput" else grep_runtime
            base = max(grep_throughput(base_path, clients, runtime), grep_throughput(keys_path, clients, runtime))
            opt = max(
                grep_throughput(rewrites_path, clients, runtime), grep_throughput(rewrites_keys_path, clients, runtime)
            )
            change = opt / base * 100
            if metric == "runtime":
                base = min(grep_runtime(base_path, clients, runtime), grep_runtime(keys_path, clients, runtime))
                opt = min(
                    grep_runtime(rewrites_path, clients, runtime), grep_runtime(rewrites_keys_path, clients, runtime)
                )
                change = 100 - opt / base * 100

            changes[dbms] = change

        if all([np.isnan(v) for v in changes.values()]):
            continue

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
        db_count = len(order) - 1 if "hyrise-int" in order else len(order)
        hatches = [None] * db_count
        colors = [c for c in Safe_10.hex_colors[:db_count]]
        if "hyrise-int" in order:
            hatches.append("/")
            colors.append(Safe_10.hex_colors[db_count - 1])

        for d, color, pos, h in zip(order, colors, group_centers, hatches):
            plt.bar(
                [pos], [changes[d]], bar_width, color=color, hatch=h, edgecolor="white", linewidth=0.0, linestyle=""
            )
            ax = plt.gca()
            if changes[d] <= 0:
                continue
            # print(config, pos, val round(val, 1))
            ax.text(
                pos,
                changes[d] - max(changes.values()) / 50,
                str(round(changes[d], 1)),
                ha="center",
                va="top",
                size=7 * 2,
                rotation=0,
                color="white",
            )

        plt.xticks(group_centers, [names[d] for d in order], rotation=0)
        ax = plt.gca()
        plt.ylabel(f"Median {metric}\nimprovement [\\%]", fontsize=8 * 2)
        #  plt.xlabel("System", fontsize=8 * 2)
        ax.tick_params(axis="both", which="major", labelsize=7 * 2, width=1, length=6, left=True, bottom=True)

        plt.grid(axis="y", visible=True)
        fig = plt.gcf()
        column_width = 3.3374
        fig_width = column_width * 2
        fig_height = column_width * 0.475 * 2 * 0.85
        fig.set_size_inches(fig_width, fig_height)
        plt.tight_layout(pad=0)

        plt.savefig(
            os.path.join(output_dir, f"systems_comparison_simple_{benchmark.lower()}_{metric}.pdf"),
            dpi=300,
            bbox_inches="tight",
            pad_inches=0.01,
        )
        plt.close()


if __name__ == "__main__":
    args = parse_args()
    main(args.data, args.output, args.metric)
