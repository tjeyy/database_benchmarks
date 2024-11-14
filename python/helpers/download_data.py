import os
import sys
import urllib.request
import zipfile


def main():
    location = (
        "https://www.dropbox.com/scl/fi/csupwxeg1lnmfknd69mj6/experiment_data.zip?rlkey=grycbrfmmrwft69jx1iuxmvwc&dl=1"
    )
    location = "https://my.hidrive.com/lnk/Q942Lh8Hz"
    file_name = "experiment_data.zip"
    data_dir = "resources/experiment_data"

    print("- Retrieving the dataset.")

    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    url = urllib.request.urlopen(location)

    meta = url.info()

    if "X-Dropbox-Content-Length" in meta:
        file_size = int(meta["X-Dropbox-Content-Length"])
    elif "Content-Length" in meta:
        file_size = int(meta["Content-Length"])
    else:
        print("- Aborting. Could not retrieve the dataset's file size.")

    file = open(file_name, "wb")

    print("- Downloading: %s (%.2f GB)" % (file_name, file_size / 1000 / 1000 / 1000))

    already_retrieved = 0
    block_size = 8192
    try:
        while True:
            buffer = url.read(block_size)
            if not buffer:
                break

            already_retrieved += len(buffer)
            file.write(buffer)
            status = r"- Retrieved %3.2f%% of the data." % (already_retrieved * 100.0 / file_size)
            status = status + chr(8) * (len(status) + 1)
            print(status, end="\r")
    except Exception:
        print("- Aborting. Something went wrong during the download.")
        os.remove(file_name)
        sys.exit(1)

    file.close()

    print()
    print("- Unzipping the file...")

    try:
        zip = zipfile.ZipFile(file_name, "r")
        zip.extractall(data_dir)
        zip.close()
    except Exception:
        print("- Aborting. Something went wrong during unzipping.")
        os.remove(file_name)
        sys.exit(3)

    os.remove(file_name)


if __name__ == "__main__":
    main()
