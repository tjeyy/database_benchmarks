#!/usr/bin/python3

import os
import string


def main():
    tables = {
        "JOB": [
            "aka_name",
            "aka_title",
            "cast_info",
            "char_name",
            "comp_cast_type",
            "company_name",
            "company_type",
            "complete_cast",
            "info_type",
            "keyword",
            "kind_type",
            "link_type",
            "movie_companies",
            "movie_info",
            "movie_info_idx",
            "movie_keyword",
            "movie_link",
            "name",
            "person_info",
            "role_type",
            "title",
        ],
        "TPC-H": ["nation", "region", "part", "supplier", "partsupp", "customer", "orders", "lineitem"],
        "TPC-DS": [
            "call_center",
            "catalog_page",
            "catalog_returns",
            "catalog_sales",
            "customer",
            "customer_address",
            "customer_demographics",
            "date_dim",
            "household_demographics",
            "income_band",
            "inventory",
            "item",
            "promotion",
            "reason",
            "ship_mode",
            "store",
            "store_returns",
            "store_sales",
            "time_dim",
            "warehouse",
            "web_page",
            "web_returns",
            "web_sales",
            "web_site",
        ],
        "SSB": ["customer", "date", "lineorder", "part", "supplier"],
    }

    seps = string.printable
    seps = ["|"]
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
                    # if sep in line:
                    #    print(sep, line)
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
