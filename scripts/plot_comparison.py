#!/usr/bin/env python3

import os
import re

import pandas as pd
import numpy as np

import math
import matplotlib.pyplot as plt
import seaborn as sns

from collections import defaultdict
from matplotlib import rc
from palettable.cartocolors.qualitative import Antique_6, Bold_6, Pastel_6, Prism_6, Safe_6, Vivid_6

import matplotlib as mpl


def to_ms(n):
    return round(n / (10**6), 2)

def per(n):
    return round(n * 100, 2)

def main():

    changes = {
        "hyrise-int": 10,
        "hyrise": 5,
        "monetdb": 4,
        "umbra": 2,
        "hana": 3,
        "greenplum": 1,
    }

    order = list(reversed(["hyrise-int", "hyrise", "hana",  "umbra", "monetdb", "greenplum"]))
    names = {
        "hyrise-int": "Hyrise\n(internal)",
        "hyrise": "Hyrise",
        "monetdb": "MonetDB",
        "umbra": "Umbra",
        "hana": "System X",
        "greenplum": "Greenplum"
    }

    sns.set()
    sns.set_theme(style="whitegrid")
    plt.rcParams["figure.figsize"] = [x * 1 for x  in plt.rcParams["figure.figsize"]]
    plt.rcParams["font.family"] = "serif"

    bar_width = 0.4
    epsilon = 0.015
    margin = 0.01


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

    group_centers = np.arange(len(order))
    offsets = [-1, 0, 1]


    # print(df2.head())

    hatches = [None, None, None, None, None,  "O"]
    colors = [c for c in Safe_6.hex_colors[:5]] + [Safe_6.hex_colors[4]]


    for d, color, pos, h in zip(order, colors, group_centers, hatches):
        plt.bar([pos], [changes[d]], bar_width, color=color, hatch=h) #, label=name) #, hatch=h, edgecolor="darkgrey")


    plt.xticks(group_centers, [names[d] for d in order], rotation=0)
    ax = plt.gca()

    box = ax.get_position()
    #ax.set_position([box.x0, box.y0, box.width, box.height])

    # plt.legend(None)
    #plt.legend(title='')
    #plt.ylim([0, 1.6])
    # sns.despine()

    #plt.xlim([-3 * bar_width, 1 + 3 * bar_width])


    plt.ylabel(r"Throughput Improvement [\%]", fontsize=8*2)
    plt.xlabel('System', fontsize=8*2)
    ax.tick_params(axis='both', which='major', labelsize=7*2)
    ax.tick_params(axis='both', which='minor', labelsize=7*2)

    plt.grid(axis="x", visible=False)


    fig = plt.gcf()
    r"""
    \usepackage{layouts}
    \printinunitsof{in}\prntlen{\columnwidth}
    """
    column_width = 3.3374
    fig_width = column_width * 2
    fig_height = column_width * 0.475 * 2
    plt.tight_layout(pad=0)
    fig.set_size_inches(fig_width, fig_height)
    # ax.set_box_aspect(1)



    plt.savefig(f"figures/systems_comparison", dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == '__main__':
    main()
