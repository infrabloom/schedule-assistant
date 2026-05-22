#!/usr/bin/env python3
"""
xer_io.py - low-level XER read / write for the change-set pipeline.

One implementation of the XER parser and writer, shared by the pipeline
scripts so a parser fix lands in exactly one place. `parse_xer` returns the
ERMHDR line, an ordered list of `Table` objects, and the source file's line
terminator; `write_xer` renders them back. Untouched rows are preserved
exactly, and the line terminator is round-tripped, so a Windows P6 export
(CRLF) and a Unix one (LF) each come back byte-faithful.

This module has no dependencies beyond the standard library and imports
nothing from the rest of the plugin - it is the bottom of the stack.
"""


class Table:
    """One XER table: a name, an ordered column list, and a list of row lists."""

    def __init__(self, name):
        self.name = name
        self.cols = []
        self.rows = []

    def g(self, row, col):
        """Get the value of `col` in `row` ('' if the row is short)."""
        i = self.cols.index(col)
        return row[i] if i < len(row) else ''

    def s(self, row, col, val):
        """Set the value of `col` in `row`, padding the row if needed."""
        i = self.cols.index(col)
        while len(row) <= i:
            row.append('')
        row[i] = val


def parse_xer(path):
    """Parse an XER file. Return (ermhdr_line, [Table, ...], newline) in file
    order. `newline` is the source line terminator ('\\r\\n' for a Windows P6
    export, '\\n' otherwise) so a later write_xer() can reproduce it exactly."""
    # read raw - newline='' disables universal-newline translation - so the
    # source line terminator can be detected, then normalise for parsing.
    with open(path, encoding='cp1252', newline='') as f:
        raw = f.read()
    newline = '\r\n' if '\r\n' in raw else '\n'
    txt = raw.replace('\r\n', '\n').replace('\r', '\n')
    ermhdr = None
    tables = []
    cur = None
    for ln in txt.split('\n'):
        if ln.startswith('ERMHDR'):
            ermhdr = ln
            continue
        if ln == '%E':
            continue
        p = ln.split('\t')
        if p[0] == '%T':
            cur = Table(p[1])
            tables.append(cur)
        elif p[0] == '%F':
            cur.cols = p[1:]
        elif p[0] == '%R':
            cur.rows.append(p[1:])
    return ermhdr, tables, newline


def write_xer(ermhdr, tables, path, newline='\n'):
    """Render (ermhdr, tables) back to an XER file at `path`. `newline` is the
    line terminator to emit - pass the value parse_xer() returned for the base
    file so the round-trip is byte-faithful (a Windows XER stays CRLF)."""
    out = [ermhdr]
    for t in tables:
        out.append('%T\t' + t.name)
        out.append('%F\t' + '\t'.join(t.cols))
        for r in t.rows:
            out.append('%R\t' + '\t'.join(r))
    out.append('%E')
    with open(path, 'w', encoding='cp1252', newline='') as f:
        f.write(newline.join(out))


def parse_rows(path):
    """Parse an XER as {table_name: [row_dict, ...]}, each row a {col: value}
    dict. This is the convenient read-only view for analysis - used by the
    verifier and the milestone forecaster. `parse_xer` returns the mutable
    Table model the patcher needs; `parse_rows` is built on top of it so there
    is still only one scanner."""
    _, tables, _ = parse_xer(path)
    return {t.name: [{c: t.g(r, c) for c in t.cols} for r in t.rows]
            for t in tables}
