import argparse as ap

from queries import static_job_queries
from pathlib import Path


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument("config", type=str, choices=["original", "hana", "hana_o3"])
    parser.add_argument("kw", type=str)
    parser.add_argument("pos", type=int)
    parser.add_argument("--range", "-r", type=int, default=10)
    return parser.parse_args()

def split_query(query):
    return [statement for statement in query.split(";") if statement.strip()]


def load_queries(directory, blacklist={}):
    queries = {}
    for filename in Path(directory).glob("*.sql"):
        if not filename.is_file() or filename.name in blacklist:
            continue

        with open(str(filename), "r") as sql_file:
            sql_query = sql_file.read()
            queries[filename.stem] = sql_query.strip()
    return queries


def main(keyword, position, lookahead, config):
    queries = None
    if config == "hana":
        queries = static_job_queries.hana_queries
    elif config == "hana_o3":
        queries == static_job_queries.hana_queries_o3
    elif config == "original":
        queries = load_queries(".", {"fkindexes.sql", "schema.sql"})



    for q_id in sorted(queries.keys()):
        query = queries[q_id]

        for item in split_query(query):
            if len(item) < position:
                continue

            start = max(0, position - lookahead)
            end = min(len(item), position + lookahead)

            if keyword not in item[start:end] and keyword != "*":
                continue

            print(q_id, "  ", item[start:end])


if __name__ == '__main__':
    args = parse_args()
    main(args.kw, args.pos, args.range, args.config)
