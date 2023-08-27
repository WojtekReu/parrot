#!/usr/bin/env python

from string import ascii_lowercase
from pathlib import Path
import typer


def repair_new_lines(filename_path):
    """
    Add END_LINE char according the rules
    """
    with open(filename_path) as f_input:
        data = f_input.read()

    newbook = ""
    print_line = ""
    for line in data.split("\n"):
        if print_line:
            print(f"{print_line} ____ {line[:20]}")
            print_line = ""
        newbook = f"{newbook}{line}"
        if (
            line
            and line[-1] in (".", "!", "?", '"', ":", "…", ")")
            or line.startswith("Chapter")
            or line.startswith("Project I")
            or line.startswith("-")
            or line.endswith("STATUS")
        ):
            newbook = f"{newbook}\n"
        else:
            end_line = True
            for c in ascii_lowercase:
                if c in line:
                    end_line = False
                    break
            if end_line:
                newbook = f"{newbook}\n"
            else:
                newbook = f"{newbook} "
                print_line = line[-50:]

    new_book_path = Path(f"NEW_{filename_path.name}")

    with open(new_book_path, "w") as f:
        f.write(newbook)


def main(
    filename_path: Path = typer.Argument(
        ...,
        help="book file in text format",
    )
):
    """
    Try to repair new lines in book.
    """
    repair_new_lines(filename_path)


if __name__ == "__main__":
    typer.run(main)
