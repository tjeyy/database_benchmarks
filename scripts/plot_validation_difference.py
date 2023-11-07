#!/usr/bin/env python3.11

import re
from collections import defaultdict

import latex
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.ticker import FuncFormatter
from palettable.cartocolors.qualitative import Safe_6


def format_number(n):
    if n < 1:
        return str(n)
    return str(int(n))

    for x in [1, 3, 5, 10]:
        if n == x:
            return str(int(n))
    return ""


def to_s(v):
    def val_to_s(x):
        return x / 10**9

    if type(v) != list:
        return val_to_s(v)
    return [val_to_s(i) for i in v]


def get_discovery_times(common_path):
    time_regexes = [
        re.compile(r"\d+(?=\ss)"),
        re.compile(r"\d+(?=\sms)"),
        re.compile(r"\d+(?=\sµs)"),
        re.compile(r"\d+(?=\sns)"),
    ]
    candidate_regex = re.compile(r"(?<=Checking )\w+(?= )")
    time_divs = list(reversed([1, 10**3, 10**6, 10**9]))
    candidte_indicator = "Checking "

    candidate_times = defaultdict(list)

    with open(common_path) as f:
        for l in f:
            # print("l")
            match = candidate_regex.search(l.strip())
            if not match:
                # print("cont")
                continue

            line = l.strip()[len(candidte_indicator) :]
            # print(line)
            candidate_time = 0
            for regex, div in zip(time_regexes, time_divs):
                r = regex.search(line)
                if not r:
                    continue
                t = int(r.group(0))
                candidate_time += t * div
            if "rejected" in line:
                status = "invalid"
            elif "confirmed" in line:
                status = "valid"
            else:
                assert "skipped" in line
                status = "skipped"

            candidate_times[status].append(candidate_time)
    return candidate_times


def main():
    commit = "64fed166781996d29745cb99d662346e18ca8d74"
    commit = "b456ab78a170a9bb38958ccebb1293e12ade555b"
    commit = "9eb09b4feceb6eeb1c2bf8229f75ef7f6f8d001a"

    benchmarks = {"TPCH": "TPC-H", "TPCDS": "TPC-DS", "StarSchema": "SSB", "JoinOrder": "JOB"}
    bens = ["TPC-H", "TPC-DS", "SSB", "JOB"]

    base_palette = Safe_6.hex_colors

    discovery_times_old = dict()
    discovery_times_new = dict()

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

    for benchmark, benchmark_title in benchmarks.items():
        sf_indicator = "" if benchmark_title == "JOB" else f"_s10"
        common_path = f"hyriseBenchmark{benchmark}_{commit}_st{sf_indicator}_plugin"
        old_path = f"naive_validation_{benchmark_title.lower().replace('-', '')}.log"
        new_path = common_path + ".log"

        discovery_times_old[benchmark_title] = get_discovery_times(old_path)
        discovery_times_new[benchmark_title] = get_discovery_times(new_path)

    def get_color(status, impl):
        if status == "skipped":
            return Safe_6.hex_colors[4]
        # valid naive = 0
        # valid meta = 1
        # invalid naiv = 2
        # invalid meta = 3
        base = 2 if impl == "optimized" else 0
        offset = 0 if status == "valid" else 1
        return Safe_6.hex_colors[base + offset]

    bar_width = 0.2
    epsilon = 0.015
    margin = 0.01

    group_centers = np.arange(len(benchmarks))
    offsets = [-0.5, 0.5]
    offsets = [-0.5, 0.5]

    sums = []

    for impl, disc_times, offset in zip(
        [r"na\"{i}ve", "optimized"], [discovery_times_old, discovery_times_new], offsets
    ):

        # print(disc_times)

        bar_positions_a = [p + 3 * offset * (bar_width + margin) for p in group_centers]
        bar_positions_b = [p + offset * (bar_width + margin) for p in group_centers]
        if impl != r"na\"{i}ve":
            bar_positions_a, bar_positions_b = [bar_positions_b, bar_positions_a]
        bar_positions_s = [(x + y) / 2 for x, y in zip(bar_positions_a, bar_positions_b)]

        # vals = [max(sum(data[b]["invalid"][impl]) / 10**6, min_val) for b in bens]
        t_invalid = [sum(disc_times[b]["invalid"]) / 10**9 for b in bens]
        # t_skip = [sum(disc_times[b]["skipped"]) / 10**9 for b in benchmarks.values()]
        t_valid = [sum(disc_times[b]["valid"]) / 10**9 for b in bens]
        t_sum = [(sum(disc_times[b]["valid"]) + sum(disc_times[b]["invalid"])) / 10**9 for b in bens]

        # t_skip = [t_invalid[i] + t_skip[i] for i in range(len(benchmarks))]
        # t_valid = [t_invalid[i] + t_valid[i] for i in range(len(bens))]
        # print(t_invalid)
        # print(t_valid)
        print([len(disc_times[b]["invalid"]) for b in bens])
        ax = plt.gca()
        ax.bar(bar_positions_s, t_sum, bar_width, color="lightgrey")
        ax.bar(bar_positions_a, t_valid, bar_width, color=get_color("valid", impl), label=f"Valid {impl}")
        # ax.bar(bar_positions, t_skip, bar_width, color=get_color("skipped", impl), label=f"Skipped")
        ax.bar(bar_positions_b, t_invalid, bar_width, color=get_color("invalid", impl), label=f"Invalid {impl}")

        sums.append((t_sum, bar_positions_s))

        for values, positions in [(t_invalid, bar_positions_b), (t_valid, bar_positions_a)]:
            for v, x in zip(values, positions):
                y = max(v, 0.005)
                if v < 0.01:
                    print(v)
                label = str(round(v, 2))
                label = label if label != "0.0" else r"$\ast$"
                # print(label)
                ax.text(x, y * 1.05, label, ha="center", va="bottom")

    max_s = max([max(s) for s, _ in sums])

    for t_sum, bar_positions_s in sums:
        for v, x in zip(t_sum, bar_positions_s):
            y = v

            label = r"$\Sigma " + str(round(v, 2)) + "$"
            # print(label)
            ax.text(x, max_s * 1.75, label, ha="center", va="top")

    min_lim = ax.get_ylim()[0]
    max_lim = ax.get_ylim()[1]

    possible_ticks_below_one = [10 ** (-exp) for exp in reversed(range(1, 2))]
    possible_ticks_above_one = [1, 3, 5, 10]
    ticks = list()
    for tick in possible_ticks_below_one:
        if tick >= min_lim:
            ticks.append(tick)
    for tick in possible_ticks_above_one:
        if tick <= max_lim:
            ticks.append(tick)
    # ticks += psossible_ticks_above_one

    ax.set_yscale("log")
    min_lim = ax.get_ylim()[0]
    max_lim = ax.get_ylim()[1]
    ax.set_ylim(0.005, max_lim * 1.5)
    ax.set_ylim(0.005, max_lim * 1.3)
    # ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: format_number(x)))

    plt.xticks(group_centers, bens, rotation=0)
    y_label = "Validation runtime [s]"
    plt.ylabel(y_label, fontsize=8 * 2)
    plt.xlabel("Benchmark", fontsize=8 * 2)
    # plt.legend(fontsize=7*2, fancybox=False, )
    plt.legend(loc="upper center", fontsize=7 * 2, ncol=2, bbox_to_anchor=(0.5, 1.3), fancybox=False, framealpha=1.0)
    plt.grid(axis="x", visible=False)
    # plt.legend(fancybox=False)
    ax.tick_params(axis="both", which="major", labelsize=7 * 2)
    ax.tick_params(axis="both", which="minor", labelsize=7 * 2)

    # ax.set_yscale('log')
    # ax.set_xscale('log')

    # if benchmark == "TPCDS":
    #    max_value = 3.99

    # min_lim = min(ax.get_ylim()[0], ax.get_xlim()[0])
    # max_lim = max(ax.get_ylim()[1], ax.get_xlim()[1])
    # plt.ylim((plt.ylim()[0], 110))
    fig = plt.gcf()

    column_width = 3.3374
    fig_width = column_width * 2
    fig_height = column_width * 0.475 * 2.5
    fig.set_size_inches(fig_width, fig_height)
    plt.tight_layout(pad=0)
    # ax.set_box_aspect(1)

    # print(os.path.join(output, f"{benchmark}_{file_indicator}_{config}_{metric}.{extension}"))
    # plt.savefig(f"benchmarks_combined_sf_{commit}_{measurement_type}.pdf", dpi=300, bbox_inches="tight")
    plt.savefig(f"validation_improvement.pdf", dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()
