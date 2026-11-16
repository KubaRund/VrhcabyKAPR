import argparse
import json
from pathlib import Path

from board import MOVE_LABELS


DEFAULT_SAVE = Path("save_file.json")


def format_move(move, *, legacy=False):
    start, end, roll, kind = move
    if not legacy:
        start = "bar" if start >= 24 else start + 1
        end = "domeček" if end >= 26 else end + 1
    return f"{start} → {end} [{roll}] · {MOVE_LABELS.get(kind, kind)}"


def format_entry(row):
    if isinstance(row, dict):
        return row["player"], format_move(row["move"])
    name, move = row
    return name, format_move(move, legacy=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Vypíše historii tahů uložené partie.")
    parser.add_argument("uloha", type=Path, nargs="?", default=DEFAULT_SAVE)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.uloha.read_text(encoding="utf-8"))
        for row in data["progress"]:
            name, description = format_entry(row)
            print(f"{name}: {description}")
    except (OSError, ValueError, IndexError, KeyError, TypeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
