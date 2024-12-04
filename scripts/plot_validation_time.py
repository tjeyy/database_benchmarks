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
    parser.add_argument("--scale", "-s", type=str, default="symlog", choices=["linear", "log", "symlog"])
    return parser.parse_args()


def format_number(n):
    return f"{int(n):,.0f}".replace(",", r"\thinspace") if n % 1 == 0 else str(n)


def main(commit, data_dir, output_dir, scale):
    sns.set_theme(style="white")

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

    benchmarks = ["TPCH", "TPCDS", "JoinOrder", "StarSchema"]
    type_regex = re.compile(r"(?<=Checking )\w+(?= )")
    time_regexes = [
        re.compile(r"\d+(?=\ss)"),
        re.compile(r"\d+(?=\sms)"),
        re.compile(r"\d+(?=\sµs)"),
        re.compile(r"\d+(?=\sns)"),
    ]
    time_divs = list(reversed([1, 10**3, 10**6, 10**9]))

    for benchmark in benchmarks:
        sf_indicator = "" if benchmark == "JoinOrder" else "_s10"
        common_path = f"hyriseBenchmark{benchmark}_{commit}_st{sf_indicator}_plugin.log"
        print(benchmark)

        candidate_times = defaultdict(list)

        with open(os.path.join(data_dir, common_path)) as f:
            for line in f:
                if not line.startswith("Checking"):
                    continue
                line = line.strip()
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
            print("   ", candidate_type, np.mean(validation_times), np.median(validation_times))
            plot_data["type"] += [f"{candidate_type}\\thinspace({candidate_count})"] * candidate_count

        print("   ", benchmark_candidates, "candidates overall")

        order = ["OD", "IND", "UCC", "FD"]

        def mapper(label):
            return order.index(label.split("\\")[0])

        unique_keys = list(sorted(set(plot_data["type"]), key=mapper))
        colors = {k: Safe_6.hex_colors[mapper(k)] for k in unique_keys}
        # print(colors)

        ax = sns.boxplot(
            data=plot_data,
            x="type",
            y="time",
            palette=colors,
            saturation=1.0,
            hue="type",
            legend=False,
            order=unique_keys,
            # boxprops={"fc": "w", "ec": "k"},
            boxprops={"ec": "k"},
            whiskerprops={"c": "k"},
            flierprops={"mfc": "k", "mec": "k"},
            medianprops={"c": "k"},
            capprops={"c": "k"},
            whis=[0, 100],
        )

        ax = plt.gca()

        y_max = max(plot_data["time"])
        y_scale_factor = 1.5
        if y_max < 0.1:
            y_scale_factor = 1.15
        y_max *= y_scale_factor
        y_max = max(0.1, y_max)

        if scale == "symlog":
            ax.set_yscale("symlog", linthresh=0.1)
        else:
            ax.set_yscale(scale)
        y_min = 0 if scale != "log" else ax.get_ylim()[0]
        ax.set_ylim(y_min, y_max)

        possible_minor_ticks = []
        if scale != "linear":
            factors = [1 / 100, 1 / 10, 1, 10, 100]
            if scale == "log":
                factors = [1 / 10000, 1 / 1000] + factors
            for factor in factors:
                possible_minor_ticks += [n * factor for n in range(1, 10)]

        minor_ticks = list()
        for tick in possible_minor_ticks:
            if tick >= y_min and tick <= y_max:
                minor_ticks.append(tick)

        plt.xlabel(r"Candidate type\thinspace($\#$)", fontsize=8 * 2)
        plt.ylabel("Validation time [ms]", fontsize=8 * 2)
        ax.tick_params(axis="y", which="major", labelsize=7 * 2, width=1, length=6, left=True)
        ax.tick_params(axis="y", which="minor", labelsize=7 * 2, width=0.5, length=4, left=True)
        ax.tick_params(axis="x", which="major", labelsize=6 * 2, width=1, length=6, bottom=True)
        if scale != "log" or y_max < 0.1:
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: format_number(x)))
        ax.yaxis.set_minor_locator(FixedLocator(minor_ticks))
        plt.grid(axis="y", visible=True)

        fig = plt.gcf()
        column_width = 3.3374
        fig_width = column_width * 0.475 * 2
        fig.set_size_inches(fig_width, fig_width)

        plt.tight_layout(pad=0)
        plt.savefig(os.path.join(output_dir, f"{benchmark}_validation_{scale}.pdf"), dpi=300, bbox_inches="tight")
        plt.close()


if __name__ == "__main__":
    args = parse_args()
    main(args.commit, args.data, args.output, args.scale)
