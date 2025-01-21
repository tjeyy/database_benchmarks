import argparse as ap
import re


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument("--sep", "-s", type=str, default="\u0007")
    return parser.parse_args()


def main(file_name, sep):
    tuples = []
    original_table_file = (
        "/Users/deyass/Documents/phd/dependency-based-optimization/resources/experiment_data/title.hana.csv"
    )

    print("Load order")
    original_order = dict()

    tid = 0
    non_esc_quote_ct = 0
    non_esc_esc_ct = 0
    non_esc_quote = re.compile(r'(?<!\+)"')
    non_esc_esc = re.compile(r'(?<!\+)\+(?!["+])')
    max_title = ""

    with open(original_table_file) as f:
        for line in f:
            non_esc_quote_ct += len(non_esc_quote.findall(line))
            non_esc_esc_ct += len(non_esc_esc.findall(line))
            t = line.strip().split(sep)
            if len(t) > 0:
                # original_order.append(int(t[0]))
                original_order[int(t[0])] = tid
                tid += 1
                if len(t[1]) > len(max_title):
                    max_title = t[1]
    print(non_esc_quote_ct, non_esc_esc_ct)
    print(len(original_order))
    print(original_order[6010], original_order[98533], original_order[98721])
    print(len(max_title), f"'{max_title}'")

    print("Load data")
    with open(file_name) as f:
        for line in f:
            t = line.strip().split(sep)
            if len(t) > 0:
                tuples.append(t)

    print("Sort")
    # tuples.sort(key=lambda t: original_order.index(int(t[0])))
    tuples.sort(key=lambda t: original_order[int(t[0])])
    print(min(int(t[0]) for t in tuples), max(int(t[0]) for t in tuples))

    new_file_name = file_name
    if file_name.endswith(".csv"):
        new_file_name = new_file_name[: -len(".csv")]
    new_file_name += ".sorted"
    if file_name.endswith(".csv"):
        new_file_name += ".csv"

    print("Write data")
    with open(new_file_name, "w") as f:
        for t in tuples:
            f.write(sep.join(t))
            f.write("\n")


if __name__ == "__main__":
    args = parse_args()
    main(args.file, args.sep)
