#!/usr/bin/python3

import os
import string


def main():
    seps = string.printable + string.whitespace
    unmachted_sep = {sep: False for sep in seps}

    for table_file in sorted([f for f in os.listdir(".") if f.endswith(".hana.csv")]):
        table_name = table_file[: -len(".hana.csv")]
        print(table_name, table_file)
        # unmachted_sep = {sep: False for sep in seps}
        with open(table_file) as f:
            for line in f:
                if "+" in line or '"' in line:
                    print(line)
                    break
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

        # if ("|") in unmachted_sep:
        #     print("|", seps.index("|"))
        #     continue

    # print(len(unmachted_sep))

    # for sep in unmachted_sep:
    #     print(sep, seps.index(sep), sep.encode())


if __name__ == "__main__":
    main()
