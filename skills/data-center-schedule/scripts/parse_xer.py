"""
parse_xer.py — generic XER reader.

Loads any P6 XER file into Python dicts for inspection / analysis.
Used as a helper by validate_xer.py, duplicate_audit.py, and any project-specific
analysis scripts.

Usage as library:
    from parse_xer import parse_xer, summary
    tables = parse_xer("path/to/Schedule.xer")
    print(summary(tables))

Usage as CLI:
    python parse_xer.py path/to/Schedule.xer
    # prints a summary of tables and counts
"""

import sys
from pathlib import Path


def parse_xer(path) -> dict:
    """Parse an XER file. Returns {table_name: list of dict rows}."""
    path = Path(path)
    text = path.read_text(encoding="cp1252", errors="replace")
    tables = {}
    current_table = None
    current_fields = None
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if line.startswith("ERMHDR"):
            tables["__header__"] = line
        elif line.startswith("%T\t"):
            current_table = line.split("\t", 1)[1].strip()
            tables[current_table] = []
            current_fields = None
        elif line.startswith("%F\t"):
            current_fields = line.split("\t")[1:]
        elif line.startswith("%R\t") and current_fields is not None:
            values = line.split("\t")[1:]
            while len(values) < len(current_fields):
                values.append("")
            tables[current_table].append(dict(zip(current_fields, values)))
        elif line.startswith("%E"):
            break
    return tables


def summary(tables: dict) -> str:
    """Return a human-readable summary of an XER's contents."""
    lines = []
    lines.append(f"Header: {tables.get('__header__', '<missing>')}")
    lines.append(f"Tables: {len([k for k in tables if not k.startswith('__')])}")
    lines.append("")
    for name in sorted(k for k in tables.keys() if not k.startswith("__")):
        rows = tables[name]
        lines.append(f"  {name:20s}  {len(rows)} rows")
    lines.append("")
    # Project info
    for p in tables.get("PROJECT", []):
        lines.append(f"Project: {p.get('proj_short_name', '')} — {p.get('name', '')}")
        lines.append(f"  Plan start: {p.get('plan_start_date', '')}")
        lines.append(f"  Plan end:   {p.get('plan_end_date', '')}")
        lines.append(f"  Recalc:     {p.get('last_recalc_date', '')}")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_xer.py path/to/Schedule.xer")
        sys.exit(2)
    tables = parse_xer(sys.argv[1])
    print(summary(tables))


if __name__ == "__main__":
    main()
