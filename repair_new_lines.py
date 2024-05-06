#!/usr/bin/env python

from string import ascii_lowercase
from pathlib import Path
import typer
import re

TABLE_OF_CONTENTS = "table of contents"
NUMBER_REPLACEMENT = "(*)"  # You can use "(*)" or just delete number ""


def read_book(input_path: Path):
    with open(input_path) as f:
        return f.read()


def write_book(content: list, output_filename: str):
    with open(Path(output_filename), "w") as f:
        f.write("\n".join(content))


def remove_numbers(line):
    return re.sub(r"(\d)+$", "", line).strip()


def repair_new_lines(content: str) -> str:
    """
    Add END_LINE char according the rules
    """
    newbook = ""
    for line in content.split("\n"):
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

    return newbook


def num_replace(matchobj):
    outer, inner = matchobj.group(0, 1)
    return outer.replace(inner, NUMBER_REPLACEMENT).strip()


def split_to_lines(content_raw: str) -> list[str]:
    content = []
    for line in content_raw.split("\n"):
        line = line.strip()
        if line:
            content.append(line)
    return content


def get_table_of_contents(content: list[str]) -> tuple[list, list]:
    """
    Separate table of contents from content
    """
    is_table_of_contents = False
    table_of_contents = []
    new_content = []
    for line in content:
        if line.lower() == TABLE_OF_CONTENTS:
            is_table_of_contents = True
            continue

        if is_table_of_contents:
            if table_of_contents and table_of_contents[0] == line:
                is_table_of_contents = False

            line = remove_numbers(line)
            if line:
                table_of_contents.append(line)
        else:
            new_content.append(line)

    return new_content, table_of_contents


def disable_footnotes(line: str, table_of_contents: list[str]) -> bool:
    if line.isdecimal():
        return True
    elif "|" in line:
        return True
    for subtitle in table_of_contents:
        if subtitle.startswith(line):
            return True
    return False


def find_footnotes(content: list[str], table_of_contens: list[str]) -> tuple[list, list]:
    """
    Separate footnotes from content
    """
    is_footnotes = False
    has_number = False
    footnotes = []
    new_content = content[:20]
    for line in content[20:]:
        if disable_footnotes(line, table_of_contens):
            is_footnotes = False
            continue

        if re.match(r"\d(\d)? .*", line):
            is_footnotes = True
            has_number = True

        if is_footnotes:
            if has_number:
                footnotes.append(line)
            else:
                footnotes[-1] = f"{footnotes[-1]} {line}"
            has_number = False
        else:
            new_content.append(line)

    return new_content, footnotes


def join_lines(content: list[str]) -> list[str]:
    """ """
    new_content = [content[0]]
    for line in content:
        if line and line[0] in ascii_lowercase:
            new_content[-1] = f"{new_content[-1]} {line}"
        else:
            new_content.append(line)

    return new_content


def replace_chars(content_raw: str) -> str:
    content_str = content_raw.replace("\uf0b7", "-")
    return content_str


def append_extra_line(content: list, line: str, line_1: str) -> str:
    """
    Add first part of line to context and return second part as str
    """
    content.append(line_1)
    return line[len(line_1) :]


def correct_lines(content: list[str], table_of_contents: list[str]):
    new_content = []
    title = content[0].upper()
    for line in content:
        if "|" in line:
            parts = line.split("|")
            for part in parts:
                part = part.strip()
                if part.isdigit():
                    continue
                elif part == title:
                    continue
                elif part in table_of_contents:
                    continue
                elif part and part[-1].isdecimal():
                    line = append_extra_line(new_content, line, " ".join(part.split()[:-1]))
                    break
                elif part.endswith(title):
                    line = append_extra_line(new_content, line, part[: -len(title)])
                    break
                else:
                    for subtitle in table_of_contents:
                        if part.endswith(subtitle):
                            line = append_extra_line(
                                new_content,
                                line,
                                part[: -len(subtitle)].rstrip(),
                            )
                            break
        new_content.append(line)

    return new_content


def replace_footnotes_numbers(content: list[str]) -> list[str]:
    new_content = []
    for line in content:
        # this regex removes more numbers than is needed.
        line = re.sub(r"[^ \t\n/\-($0-9A-Z](\d(\d)?)[^)$.a-zA-Z0-9]", num_replace, line)
        new_content.append(line)
    return new_content


def main(
    filename_path: Path = typer.Argument(
        ...,
        help="book file in text format",
    ),
    write_to_file: str = typer.Argument(
        ...,
        help="write content to new file",
    ),
):
    """
    Try to repair new lines in book.
    """
    content_raw = read_book(filename_path)
    # content_str = repair_new_lines(content_raw)
    content_str = replace_chars(content_raw)
    content = split_to_lines(content_str)
    content, table_of_contents = get_table_of_contents(content)
    content = correct_lines(content, table_of_contents)
    content, footnotes = find_footnotes(content, table_of_contents)
    content = replace_footnotes_numbers(content)
    content = join_lines(content)
    content += footnotes
    write_book(content, write_to_file)


if __name__ == "__main__":
    typer.run(main)
