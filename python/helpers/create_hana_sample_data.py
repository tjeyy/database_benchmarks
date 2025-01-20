def main(separator, escape):
    lines = [
        f"not quoted string",
        f"string with escape {escape}{escape} in between",
        f"string with runaway escape {escape} in between",
        f'"quoted string"',
        f'""double quoted string""',
        f'"{escape}"double quoted escaped string{escape}""',
        f"escaped{escape}{escape}string",
        f'string with "quotes" inbetween',
        f'string with {escape}"escaped quotes{escape}" inbetween',
        f'string with ""double quotes"" inbetween',
        f'string with {escape}"{escape}"escaped double quotes{escape}"{escape}" inbetween',
        f'"quoted string with "quotes" inbetween"',
        f'"quoted string with {escape}"escaped quotes{escape}" inbetween"',
        f'"quoted string with ""double quotes"" inbetween"',
        f'"quoted string with {escape}"{escape}"escaped double quotes{escape}"{escape}" inbetween"',
    ]
    with open("sample_data.csv", "w") as f:
        for tid, value in enumerate(lines):
            f.write(separator.join([str(tid), value]))
            f.write("\n")


if __name__ == "__main__":
    main("\u0007", "+")
