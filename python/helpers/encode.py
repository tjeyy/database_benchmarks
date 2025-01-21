#!/usr/bin/python3

import csv
import json

import pandas as pd


def parse_data_type(type_string):
    if type_string == "int":
        return "Int32"
    elif type_string == "long":
        return "Int64"
    elif type_string == "float":
        return "Float32"
    elif type_string == "double":
        return "Float64"
    elif type_string == "string":
        return "string"
    raise AttributeError(f"Unknown data type: '{type_string}'")


def parse_csv_meta(meta):
    column_names = list()
    column_data_types = dict()
    nullable = dict()
    for column_meta in meta["columns"]:
        column_name = column_meta["name"]
        column_names.append(column_name)
        column_data_types[column_name] = parse_data_type(column_meta["type"])
        nullable[column_name] = column_meta["nullable"]
    return column_names, column_data_types, nullable


def main():
    tables = ["keyword"]
    tables = [
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
    ]

    data_path = "."

    for i, table_name in enumerate(tables):
        print(f"{i+1}/{len(tables)}", table_name)
        new_file_path = f"{data_path}/{table_name}.hana.csv"
        table_file_path = f"{data_path}/{table_name}.csv"
        with open(table_file_path + ".json") as f:
            meta = json.load(f)

        column_names, column_types, nullable = parse_csv_meta(meta)
        data = pd.read_csv(table_file_path, header=None, names=column_names, dtype=column_types, keep_default_na=False)
        data.to_csv(
            new_file_path,
            sep="\u0007",
            header=False,
            index=False,
            escapechar="+",
            quoting=csv.QUOTE_NONE,
            quotechar='"',
        )

        data = None
        with open(new_file_path) as f:
            data = f.read()
        data = data.replace('"', '+"')
        with open(new_file_path, "w") as f:
            f.write(data)

        with open(new_file_path) as f:
            data = f.read()
            print("   ", data.count('"'), data.count("+"))


if __name__ == "__main__":
    main()
