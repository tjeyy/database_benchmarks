import argparse as ap


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument("--sep", "-s", type=str, default="\u0007")
    return parser.parse_args()


def main(file_name, sep):
    tuples = []
    with open(file_name) as f:
        for line in f:
            t = line.strip().split(sep)
            if len(t) > 0:
                tuples.append(t)
    tuples.sort(key=lambda t: int(t[0]))

    new_file_name = file_name
    if file_name.endswith(".csv"):
        new_file_name = new_file_name[: -len(".csv")]
    new_file_name += ".sorted"
    if file_name.endswith(".csv"):
        new_file_name += ".csv"

    with open(new_file_name, "w") as f:
        for t in tuples:
            f.write(sep.join(t))
            f.write("\n")


if __name__ == "__main__":
    args = parse_args()
    main(args.file, args.sep)
