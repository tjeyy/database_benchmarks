#!/usr/bin/env python3.11

import argparse as ap
import os
import re
from collections import defaultdict

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.ticker import FuncFormatter


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("commit", type=str)
    parser.add_argument("--data", "-d", type=str, default="./hyrise/cmake-build-release/benchmark_plugin_results")
    parser.add_argument("--output", "-o", type=str, default="./figures")
    return parser.parse_args()


def format_number(n):
    if n > 0 and n < 1:
        return str(n)
    return f"{int(n):,.0f}".replace(",", r"\thinspace")


def main(commit, data_dir, output_dir):
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
            plot_data["type"] += [f"{candidate_type} ({candidate_count})"] * candidate_count

        print("   ", benchmark_candidates, "candidates overall")

        order = ["OD", "IND", "UCC", "FD"]
        unique_keys = sorted(set(plot_data["type"]), key=lambda x: order.index(x.split(" ")[0]))

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

        ax = plt.gca()
        y_max = max(max(plot_data["time"]) * 1.5, 10)
        y_max = max(plot_data["time"]) * 1.5
        ax.set_yscale("symlog", linthresh=0.1)
        ax.set_ylim(0, y_max)

        plt.xlabel("Candidate type ($\\#$)", fontsize=8 * 2)
        plt.ylabel("Validation time [ms]", fontsize=8 * 2)
        ax.tick_params(axis="both", which="major", labelsize=6 * 2)
        ax.tick_params(axis="both", which="minor", labelsize=6 * 2)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: format_number(x)))

        fig = plt.gcf()
        column_width = 3.3374
        fig_width = column_width * 0.475 * 2
        fig.set_size_inches(fig_width, fig_width)

        plt.tight_layout(pad=0)
        plt.savefig(os.path.join(output_dir, f"{benchmark}_validation.pdf"), dpi=300, bbox_inches="tight")
        plt.close()


if __name__ == "__main__":
    args = parse_args()
    main(args.commit, args.data, args.output)
