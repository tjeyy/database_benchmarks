#!/usr/bin/env python3
import requests

from datetime import date, timedelta


def main():

    start_date = date.fromisoformat("2023-10-09")
    # start_date = date.fromisoformat("2023-04-21")
    end_date = date.fromisoformat("2023-04-19")


    current_date = start_date

    headers = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0"}

    while current_date > end_date:
        current_date = current_date - timedelta(days=1)
        url = f"https://db.in.tum.de/~fent/umbra-{current_date.isoformat()}-nouring.tar.xz"
        r = requests.get(url)
        if r.status_code == 200:
            print(url, r.status_code)





if __name__ == '__main__':
    main()
