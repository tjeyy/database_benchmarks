import argparse as ap

import pandas as pd


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("system", type=str)
    return parser.parse_args()


def get_median(system_name, config):
    data = pd.read_csv(f"database_comparison__all__{system_name}{config}.csv")
    assert len(data.CLIENTS.unique()) == 1 and data.CLIENTS.unique()[0] == 32
    return data.RUNTIME_MS.median() / 1000


def perc(old, new):
    deviation = 100 - new / old * 100
    prefix = "+" if deviation > 0 else ""
    return f"{prefix}{round(deviation, 1)}%"


def main(system_name):
    baseline = get_median(system_name, "")
    keys = get_median(system_name, "__keys")
    rewrites = get_median(system_name, "__rewrites")
    rewrites_keys = get_median(system_name, "__rewrites__keys")

    legend = ["Baseline", "PK & FK", "Rewrites", "PK & FK + Rewrites"]
    values = [
        f"{round(baseline, 2)}s",
        f"{round(keys, 2)}s ({perc(baseline, keys)})",
        f"{round(rewrites, 2)}s ({perc(baseline, rewrites)})",
        f"{round(rewrites_keys, 2)}s ({perc(baseline, rewrites_keys)})",
    ]

    if system_name == "hyrise":
        legend.append("Optimizer")
        optimizer = get_median(system_name, "-int")
        values.append(f"{round(optimizer, 2)}s ({perc(baseline, optimizer)})")

    max_lens = [max(len(a), len(b)) for a, b in zip(legend, values)]
    print("        ".join([v.ljust(l) for v, l in zip(legend, max_lens)]))
    print("        ".join([v.ljust(l) for v, l in zip(values, max_lens)]))


if __name__ == "__main__":
    main(parse_args().system)
