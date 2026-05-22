"""
sanitize_xer.py -- strip a real project XER down to a reusable, client-safe template.

Operations:
  1. Rename the PROJECT (proj_short_name, name) to a generic template label.
  2. Reset all actuals (status -> TK_NotStart, clear act_start/act_end, pct=0,
     remain = target).
  3. Apply the config's find/replace map to EVERY non-GUID field of EVERY table
     (activity names + codes, WBS names, calendar names, OBS / activity-code /
     category / UDF-label names -- anywhere a client / contractor / site name
     can hide).
  4. Genericize export-user / creator fields (ERMHDR user, create_user,
     update_user, add_by_name).
  5. Strip costs on TASKRSRC rows.
  6. Regenerate all GUIDs (so the template can coexist with the original in OPC).
  7. Optionally re-baseline target dates by a day offset.

GUID fields are deliberately skipped by the find/replace step -- a random
base64 GUID can contain a 3-letter token (AWS, IAD, SBN) as a coincidental
substring; replacing inside it would corrupt the GUID.

Usage:
    python sanitize_xer.py input.xer output.xer --config scrub-config.json
    python sanitize_xer.py input.xer output.xer --print-default-config

Config (JSON): template_name, template_short_name, replacements {find: rep},
reset_actuals, regenerate_guids, strip_costs, rebase_target_dates_offset_days.
List longer / more-specific find strings BEFORE shorter ones -- replacements
apply in order.
"""

import argparse
import base64
import collections
import datetime as dt
import json
import sys
import uuid
from pathlib import Path

USER_FIELDS = ("create_user", "update_user", "add_by_name")
COST_FIELDS = ("target_cost", "act_cost", "act_reg_cost", "act_ot_cost",
               "remain_cost", "act_this_per_cost", "cost_per_qty", "cost_per_qty2")
DATE_FIELDS = ("cstr_date", "cstr_date2", "target_start_date", "target_end_date",
               "early_start_date", "early_end_date", "late_start_date",
               "late_end_date", "rem_late_start_date", "rem_late_end_date",
               "expect_end_date", "external_early_start_date", "external_late_end_date")


def make_guid():
    return base64.b64encode(uuid.uuid4().bytes).decode("ascii").rstrip("=")


def sanitize(input_path: Path, output_path: Path, config: dict):
    text = input_path.read_text(encoding="cp1252", errors="replace")

    replacements = {k: v for k, v in config.get("replacements", {}).items() if k}
    reset_actuals = config.get("reset_actuals", True)
    regenerate_guids = config.get("regenerate_guids", True)
    strip_costs = config.get("strip_costs", True)
    rebase_offset = config.get("rebase_target_dates_offset_days")
    template_name = config.get("template_name")
    template_short_name = config.get("template_short_name")

    def apply_repl(s):
        for find, rep in replacements.items():
            s = s.replace(find, rep)
        return s

    table_headers = {}
    current_table = None
    counts = collections.Counter()
    out = []

    for raw in text.split("\n"):
        line = raw.rstrip("\r")

        if line.startswith("ERMHDR"):
            parts = line.split("\t")
            if len(parts) > 5:
                parts[4] = "user"
                parts[5] = "DC Schedule Template"
            out.append("\t".join(parts))
            continue
        if line.startswith("%T\t"):
            current_table = line.split("\t", 1)[1].strip()
            out.append(line)
            continue
        if line.startswith("%F\t"):
            table_headers[current_table] = line.split("\t")[1:]
            out.append(line)
            continue
        if line.startswith("%R\t") and current_table in table_headers:
            fields = table_headers[current_table]
            values = line.split("\t")[1:]
            while len(values) < len(fields):
                values.append("")
            row = dict(zip(fields, values))

            # 1. global find/replace on every non-GUID field
            for fname in fields:
                if "guid" in fname.lower():
                    continue
                if row[fname]:
                    row[fname] = apply_repl(row[fname])

            # 2. genericize export-user / creator fields
            for fname in USER_FIELDS:
                if fname in row and row[fname]:
                    row[fname] = "user"

            # 3. table-specific handling
            if current_table == "PROJECT":
                if template_short_name and "proj_short_name" in row:
                    row["proj_short_name"] = template_short_name
                if template_name and "name" in row:
                    row["name"] = template_name
                if regenerate_guids and "guid" in row:
                    row["guid"] = make_guid()
                counts["PROJECT"] += 1
            elif current_table == "PROJWBS":
                if regenerate_guids and "guid" in row:
                    row["guid"] = make_guid()
                counts["PROJWBS"] += 1
            elif current_table == "TASK":
                if reset_actuals:
                    row["status_code"] = "TK_NotStart"
                    for z in ("act_start_date", "act_end_date", "restart_date",
                              "reend_date", "suspend_date", "resume_date"):
                        if z in row:
                            row[z] = ""
                    for z in ("phys_complete_pct", "act_work_qty", "act_equip_qty",
                              "act_this_per_work_qty", "act_this_per_equip_qty"):
                        if z in row:
                            row[z] = "0"
                    if "target_drtn_hr_cnt" in row:
                        row["remain_drtn_hr_cnt"] = row.get("target_drtn_hr_cnt", "0")
                    if "target_work_qty" in row:
                        row["remain_work_qty"] = row.get("target_work_qty", "0")
                    if "target_equip_qty" in row:
                        row["remain_equip_qty"] = row.get("target_equip_qty", "0")
                if rebase_offset is not None:
                    delta = dt.timedelta(days=rebase_offset)
                    for fname in DATE_FIELDS:
                        val = row.get(fname, "").strip()
                        if val:
                            try:
                                d = dt.datetime.strptime(val[:16], "%Y-%m-%d %H:%M")
                                row[fname] = (d + delta).strftime("%Y-%m-%d %H:%M")
                            except ValueError:
                                pass
                if regenerate_guids and "guid" in row:
                    row["guid"] = make_guid()
                counts["TASK"] += 1
            elif current_table == "TASKRSRC" and strip_costs:
                for fname in COST_FIELDS:
                    if fname in row and row[fname]:
                        row[fname] = "0"
                counts["TASKRSRC"] += 1
            elif current_table == "TASKPRED":
                counts["TASKPRED"] += 1

            out.append("%R\t" + "\t".join(row.get(f, "") for f in fields))
            continue

        out.append(line)

    output_path.write_text("\n".join(out), encoding="cp1252")

    print(f"Wrote {output_path}")
    print(f"  Replacements: {len(replacements)} applied globally (all non-GUID fields)")
    print(f"  Export-user / creator fields genericized")
    if reset_actuals:
        print(f"  Reset actuals on {counts['TASK']} TASK rows")
    if regenerate_guids:
        print(f"  Regenerated GUIDs on PROJECT + PROJWBS + TASK")
    if strip_costs:
        print(f"  Stripped costs on {counts['TASKRSRC']} TASKRSRC rows")
    if rebase_offset is not None:
        print(f"  Re-baselined target dates by {rebase_offset} days")
    print()
    print("Next steps:")
    print(f"  1. Sweep {output_path.name} for any leftover client-confidential strings")
    print(f"  2. Run: python validate_xer.py {output_path}")
    print(f"  3. If acceptable, drop into assets/p6-templates/ and repackage the skill")


def make_default_config(input_path: Path) -> dict:
    return {
        "template_name": "Hyperscale-DC-Template",
        "template_short_name": "DC-TMPL",
        "replacements": {
            "_comment": "find -> generic replacement; list longer strings first",
            "Full Client Name": "OWNER",
            "GC Name": "GC",
            "Site/Geographic Name": "SITE-LOC"
        },
        "reset_actuals": True,
        "regenerate_guids": True,
        "strip_costs": True,
        "rebase_target_dates_offset_days": None
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="Source XER (real project)")
    parser.add_argument("output", help="Destination XER (sanitized template)")
    parser.add_argument("--config", help="JSON config file with replacements + flags")
    parser.add_argument("--print-default-config", action="store_true",
                        help="Print a starter config JSON and exit")
    args = parser.parse_args()

    if args.print_default_config:
        print(json.dumps(make_default_config(Path(args.input)), indent=2))
        return

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        print(f"Input not found: {input_path}", file=sys.stderr)
        sys.exit(2)

    if args.config:
        config = json.loads(Path(args.config).read_text())
        if "replacements" in config:
            config["replacements"] = {k: v for k, v in config["replacements"].items()
                                      if not k.startswith("_")}
    else:
        config = {"reset_actuals": True, "regenerate_guids": True, "strip_costs": True}

    sanitize(input_path, output_path, config)


if __name__ == "__main__":
    main()
