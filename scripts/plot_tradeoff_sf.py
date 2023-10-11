#!/usr/bin/env python3.11

import os
import re
import json

import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import seaborn as sns
import latex
import math

from collections import defaultdict
from matplotlib import rc
from matplotlib.ticker import MaxNLocator, FixedLocator, FuncFormatter

import matplotlib as mpl


from palettable.cartocolors.qualitative import Antique_6, Bold_6, Pastel_6, Prism_6, Safe_6, Vivid_6

def format_number(n):
    if n < 1:
        return str(n)
    return str(int(n))

    for x in [1,3,5,10]:
        if n == x:
            return str(int(n))
    return ""


def to_s(v):
    val_to_s = lambda x: x / 10**9
    if type(v) != list:
        return val_to_s(v)
    return [val_to_s(i) for i in v]


def get_latencies(old_path, new_path):
    with open(old_path) as old_file:
        old_data = json.load(old_file)

    with open(new_path) as new_file:
        new_data = json.load(new_file)

    if old_data["context"]["benchmark_mode"] != new_data["context"]["benchmark_mode"]:
        exit("Benchmark runs with different modes (ordered/shuffled) are not comparable")

    old_latencies = list()
    new_latencies = list()


    for old, new in zip(old_data["benchmarks"], new_data["benchmarks"]):
        name = old["name"]
        # Create numpy arrays for old/new successful/unsuccessful runs from benchmark dictionary
        old_successful_durations = np.array([run["duration"] for run in old["successful_runs"]], dtype=np.float64)
        new_successful_durations = np.array([run["duration"] for run in new["successful_runs"]], dtype=np.float64)
        old_unsuccessful_durations = np.array([run["duration"] for run in old["unsuccessful_runs"]], dtype=np.float64)
        new_unsuccessful_durations = np.array([run["duration"] for run in new["unsuccessful_runs"]], dtype=np.float64)
        # np.mean() defaults to np.float64 for int input
        #if "TPCDS" in old_path and "95" in name:
        #    print("TPC-DS Q 95", to_s([np.mean(old_successful_durations), np.mean(new_successful_durations)]))
        #    # continue
        old_latencies.append(np.mean(old_successful_durations))
        new_latencies.append(np.mean(new_successful_durations))

    return sum(old_latencies), sum(new_latencies)


def get_discovery_time(common_path):
    time_regexes = [re.compile(r'\d+(?=\ss)'), re.compile(r'\d+(?=\sms)'), re.compile(r'\d+(?=\sµs)'), re.compile(r'\d+(?=\sns)')]
    time_divs = list(reversed([1, 10**3, 10**6, 10**9]))
    discovery_time_indicator = "Executed dependency discovery in "

    with open(common_path) as f:
        for l in f:
            if not l.startswith(discovery_time_indicator):
                continue
            line = l.strip()[len(discovery_time_indicator):]
            candidate_time = 0
            for regex, div in zip(time_regexes, time_divs):
                r = regex.search(line)
                if not r:
                    continue
                t = int(r.group(0))
                candidate_time += t * div

            return candidate_time


def main():
    commit = "64fed166781996d29745cb99d662346e18ca8d74"
    commit = "b456ab78a170a9bb38958ccebb1293e12ade555b"
    commit = "9eb09b4feceb6eeb1c2bf8229f75ef7f6f8d001a"

    benchmarks = {"TPCH": "TPC-H", "TPCDS": "TPC-DS", "StarSchema": "SSB"}
    all_scale_factors = range(1, 101)

    base_palette = Safe_6.hex_colors

    latency_improvements = defaultdict(list)
    discovery_times = defaultdict(list)
    scale_factors = list()
    latency_improvements_relative = defaultdict(list)
    discovery_times_relative = defaultdict(list)


    for scale_factor in all_scale_factors:
        sf_indicator = "" if scale_factor == 10 else f"_s{scale_factor}"
        sf_indicator = f"_s{scale_factor}"
        if not os.path.isfile(f"hyriseBenchmarkTPCH_{commit}_st{sf_indicator}.log"):
            continue

        scale_factors.append(scale_factor)

        for benchmark, benchmark_title in benchmarks.items():
            common_path = f"hyriseBenchmark{benchmark}_{commit}_st{sf_indicator}"
            old_path = common_path + ".json"
            new_path = common_path + "_plugin.json"

            old_latency, new_latency = get_latencies(old_path, new_path)
            discovery_time = get_discovery_time(f"{common_path}_plugin.log")

            latency_improvements[benchmark_title].append(to_s(old_latency - new_latency))
            discovery_times[benchmark_title].append(to_s(discovery_time))

            latency_improvements_relative[benchmark_title].append((old_latency - new_latency) * 100 / old_latency)
            discovery_times_relative[benchmark_title].append(discovery_time * 100 / old_latency)

    print(scale_factors)

    for measurement_type, lat_improvements, disc_times in zip(["abs", "rel"], [latency_improvements, latency_improvements_relative], [discovery_times, discovery_times_relative]):
        sns.set()
        sns.set_theme(style="whitegrid")
        # plt.style.use('seaborn-colorblind')
        #plt.rcParams['text.usetex'] = True
        #plt.rcParams["font.family"] = "serif"

        mpl.use('pgf')

        plt.rcParams.update({
        "font.family": "serif",  # use serif/main font for text elements
        "text.usetex": True,     # use inline math for ticks
        "pgf.rcfonts": False,    # don't setup fonts from rc parameters
        "pgf.preamble":  r"""\usepackage{iftex}
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
      \fi"""
        })

        x_axis_sf = list()
        y_axis_time = list()
        indicator_measurement = list()
        indicator_benchmark = list()

        for benchmark, latency_improvement in lat_improvements.items():
            discovery_time = disc_times[benchmark]
            assert len(discovery_time) == len(latency_improvement) and len(discovery_time) == len(scale_factors)

            x_axis_sf += scale_factors * 2

            y_axis_time += latency_improvement
            y_axis_time += discovery_time

            indicator_measurement += ["Latency Improvement"] * len(latency_improvement)
            indicator_measurement += ["Discovery Time"] * len(discovery_time)

            indicator_benchmark += [benchmark] * len(scale_factors) * 2

        assert len(x_axis_sf) == len(y_axis_time) and len(x_axis_sf) == len(indicator_measurement) and len(x_axis_sf) == len(indicator_benchmark)

        values = pd.DataFrame(data={"x": x_axis_sf, "y": y_axis_time, "Measurement": indicator_measurement, "Benchmark": indicator_benchmark})

        dashes = {"Discovery Time": (3, 3), "Latency Improvement": ""}
        markers = ["^", "X", "s", "D", ".", "o"]

        sns.lineplot(data=values, x="x", y="y", style="Measurement", markers=markers[:2], hue="Benchmark", dashes=dashes, palette=base_palette[:len(benchmarks)])

        ax = plt.gca()

        y_label = 'Runtime [s]' if measurement_type == 'abs' else 'Share of Runtime [%]'
        plt.ylabel(y_label, fontsize=8*2)
        plt.xlabel('Scale factor', fontsize=8*2)
        ax.tick_params(axis='both', which='major', labelsize=7*2)
        ax.tick_params(axis='both', which='minor', labelsize=7*2)

        #ax.set_yscale('log')
        #ax.set_xscale('log')

        #if benchmark == "TPCDS":
        #    max_value = 3.99


        min_lim = min(ax.get_ylim()[0], ax.get_xlim()[0])
        max_lim = max(ax.get_ylim()[1], ax.get_xlim()[1])
        if benchmark == "StarSchema":
            max_lim = 6

        possible_ticks_below_one = [10**(-exp) for exp in reversed(range(1, 4))]
        possible_ticks_above_one = [1, 3, 5, 10]
        ticks = list()
        for tick in possible_ticks_below_one:
            if tick >= min_lim:
                ticks.append(tick)
        for tick in possible_ticks_above_one:
            if tick <= max_lim:
                ticks.append(tick)
        #ticks += psossible_ticks_above_one
        #print(min_lim, max_lim, ticks)
        #ax.set_ylim(min_lim, max_lim)
        #ax.set_xlim(min_lim, max_lim)


        #ax.set_ylim(0, max_value)
        #ax.set_xlim(0, max_value)
        #ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        #ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        #ax.xaxis.set_major_locator(FixedLocator(ticks))
        #ax.yaxis.set_major_locator(FixedLocator(ticks))
        #ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: format_number(x)))
        #ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: format_number(x)))
        fig = plt.gcf()
        r"""
        \usepackage{layouts}
        \printinunitsof{in}\prntlen{\columnwidth}
        """
        column_width = 3.3374
        fig_width = column_width * 2
        fig_height = column_width * 0.475 * 2
        fig.set_size_inches(fig_width, fig_height)
        # ax.set_box_aspect(1)


        plt.tight_layout(pad=0)
        # print(os.path.join(output, f"{benchmark}_{file_indicator}_{config}_{metric}.{extension}"))
        plt.savefig(f"benchmarks_combined_sf_{commit}_{measurement_type}.pdf", dpi=300, bbox_inches="tight")
        plt.close()

if __name__ == '__main__':
    main()
