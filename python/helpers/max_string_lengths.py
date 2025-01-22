import argparse as ap
import re


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument("--sep", "-s", type=str, default="\u0007")
    return parser.parse_args()


def main(file_name, sep):
    max_lens = None
    max_vals = None
    vals_over_1024 = None

    with open(file_name) as f:
        for line in f:
            t = line.strip().split(sep)
            if len(t) > 0:
                if max_lens is None:
                    max_lens = [0 for _ in range(len(t))]
                    vals_over_1024 = [0 for _ in range(len(t))]
                    max_vals = ["" for _ in range(len(t))]
                # print(max_lens)
                # print(t)
                max_lens = [max(x, len(y)) for x, y in zip(max_lens, t)]
                max_vals = [x if len(x) > len(y) else y for x, y in zip(max_vals, t)]
                vals_over_1024 = [x if len(y) <= 1024 else x + 1 for x, y in zip(vals_over_1024, t)]

    print(max_lens)
    print(vals_over_1024)

    # for s in max_vals:
    #     print("")
    #     print(s)


if __name__ == "__main__":
    args = parse_args()
    main(args.file, args.sep)
