#!/usr/bin/python3

import os
import string


def main():
    seps = string.printable
    unmachted_sep = {sep: False for sep in seps}

    for table_file in sorted([f for f in os.listdir(".") if f.endswith(".csv")]):
        table_name = table_file[: -len(".csv")]
        print(table_name)
        unmachted_sep = {sep: False for sep in seps}
        with open(f"{table_name}.csv") as f:
            for line in f:
                found_seps = list()
                for sep, found in unmachted_sep.items():
                    if found:
                        continue
                    if sep in line:
                        found_seps.append(sep)
                for sep in found_seps:
                    del unmachted_sep[sep]
                    if len(unmachted_sep) == 0:
                        break

        if ("|") in unmachted_sep:
            print("|", seps.index("|"))
            continue

        for sep in unmachted_sep:
            print(sep, seps.index(sep))


if __name__ == "__main__":
    main()
