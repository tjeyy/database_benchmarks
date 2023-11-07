#!/usr/bin/env python3

import argparse as ap
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from palettable.cartocolors.qualitative import Safe_6


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("--output", "-o", type=str, default="./figures")
    return parser.parse_args()


def to_ms(n):
    return round(n / (10**6), 2)


def per(n):
    return round(n * 100, 2)


def main(output_dir):
    regular = {
        "TPC-DS Q26": 209395576.670000,
        "TPC-DS Q37": 552702500.750000,
        "TPC-DS Q82": 611591275.050000,
        "TPC-DS Q85": 192611687.840000,
        "JOB Q13a": 315036292.200000,
        "JOB Q22c": 658473615.380000,
        "JOB Q28a": 409619709.580000,
    }

    rewritten = {
        "TPC-DS Q26": 73273516.920000,
        "TPC-DS Q37": 54757805.120000,
        "TPC-DS Q82": 109594167.260000,
        "TPC-DS Q85": 1607530957.790000,
        "JOB Q13a": 180239615.460000,
        "JOB Q22c": 436048116.200000,
        "JOB Q28a": 932455632.540000,
    }

    optimized = {
        "TPC-DS Q26": 75057740.440000,
        "TPC-DS Q37": 53276721.910000,
        "TPC-DS Q82": 113223823.040000,
        "TPC-DS Q85": 102627679.340000,
        "JOB Q13a": 130065924.710000,
        "JOB Q22c": 232982224.640000,
        "JOB Q28a": 202094889.490000,
    }

    for query, reg in regular.items():
        print(f"{query}: {to_ms(reg)} ms / {per(rewritten[query] / reg)} / {per(optimized[query] / reg)} ")

    chosen = ["TPC-DS Q37", "JOB Q22c"]

    sns.set()
    sns.set_theme(style="whitegrid")
    plt.rcParams["font.family"] = "serif"

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

    bar_width = 0.2
    margin = 0.01

    group_centers = np.arange(len(chosen))
    offsets = [-1, 0, 1]

    for opt, color, offset, name in zip(
        [regular, rewritten, optimized],
        Safe_6.hex_colors[:3],
        offsets,
        ["Baseline", "External rewrite", "Internal optimization"],
    ):
        bar_positions = [p + offset * (bar_width + margin) for p in group_centers]
        vals = [opt[b] / 10**6 for b in chosen]

        plt.bar(bar_positions, vals, bar_width, color=color, label=name)

    plt.xticks(group_centers, chosen, rotation=0)
    ax = plt.gca()
    plt.legend(loc="upper center", fontsize=8 * 2, ncol=3, bbox_to_anchor=(0.5, 1.25), fancybox=False)
    plt.xlim([-3 * bar_width, 1 + 3 * bar_width])
    plt.ylabel("Latency [ms]", fontsize=8 * 2)
    plt.xlabel("Query", fontsize=8 * 2)
    ax.tick_params(axis="both", which="major", labelsize=7 * 2)
    ax.tick_params(axis="both", which="minor", labelsize=7 * 2)
    plt.grid(axis="x", visible=False)
    fig = plt.gcf()
    column_width = 3.3374
    fig_width = column_width * 2
    fig_height = column_width * 0.475 * 2
    fig.set_size_inches(fig_width, fig_height)
    plt.tight_layout(pad=0)

    plt.savefig(os.path.join(output_dir, "motivational_example.pdf"), dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main(parse_args().output)
