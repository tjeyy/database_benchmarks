import argparse as ap
import re


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument("--sep", "-s", type=str, default="\u0007")
    return parser.parse_args()


def main(file_name, sep):
    ids = set()

    with open(file_name) as f:
        for line in f:
            t = line.strip().split(sep)
            if len(t) > 0:
                ids.add(int(t[0]))
    print(len(ids), min(ids), max(ids))

    for i in range(1, max(ids)):
        if i not in ids:
            print(i)


if __name__ == "__main__":
    args = parse_args()
    main(args.file, args.sep)
