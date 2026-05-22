"""
crosscheck_msp.py -- compare Duration vs planned Start/Finish vs %complete on an
MSP XML trade schedule, and compute conversion to our 8h/day work-hour basis.

Key mechanical fact: in MSP XML, <Duration> PT-hours = (displayed days) x (MinutesPerDay/60).
  MinutesPerDay=1440  -> PT_h / 24 = days  (24h-day basis, common for continuous-occupancy schedules)
  MinutesPerDay=600   -> PT_h / 10 = days  (10h-day basis)
  MinutesPerDay=480   -> PT_h /  8 = days  (8h-day basis -- matches a standard P6 5-day schedule)
Our XER is an 8h/day calendar; conversion factor = 8 / (MinutesPerDay/60).
"""
from datetime import datetime
from parse_msp import load, code_of

# Usage:  python crosscheck_msp.py <msp.xml> [-- <name_substring> ...]
# Pass activity-name substrings as args to filter the report.
import sys
WANTED = sys.argv[2:] if len(sys.argv) > 2 else []

def span_h(a, b):
    if a and b and b > a:
        return round((b - a).total_seconds() / 3600.0, 1)
    return None

path = sys.argv[1] if len(sys.argv) > 1 else None
if not path:
    print("usage: python crosscheck_msp.py <msp.xml> [<name_substr> ...]")
    sys.exit(2)
import os
for path in [path]:
    p = load(path)
    mpd = float(p.header["MinutesPerDay"]) / 60.0   # hours per "day" in this file
    fn = path.split("/")[-1]
    print("=" * 96)
    print(f"{fn}   MinutesPerDay={p.header['MinutesPerDay']}  (PT-hours / {mpd:.0f} = days)")
    print("=" * 96)
    real = [t for t in p.tasks if t["Summary"] != "1" and t["Milestone"] != "1"]
    for t in real:
        nm = t["Name"]
        if not any(w.lower() in nm.lower() for w in WANTED):
            continue
        d_h = t["Duration_h"]
        days = (d_h / mpd) if d_h else None
        our_A = round(days * 8, 0) if days is not None else None      # day-for-day -> 8h
        our_B = round(d_h * 40.0 / 168.0, 0) if d_h else None         # 24/7 footprint -> 5d/8h
        sp = span_h(t["Start_dt"], t["Finish_dt"])
        ad, rd = t["ActualDuration_h"], t["RemainingDuration_h"]
        pct = t["PercentComplete"]
        # consistency: does Start->Finish span match Duration? does AD+RD match D?
        sf_flag = ""
        if sp and d_h:
            if abs(sp - d_h) <= 0.05 * d_h:
                sf_flag = "span==Dur(24/7)"
            else:
                sf_flag = f"span {sp:.0f}h != Dur {d_h:.0f}h"
        adrd = ""
        if d_h and ad is not None and rd is not None:
            adrd = "AD+RD==D" if abs((ad + rd) - d_h) <= max(1, 0.02*d_h) else f"AD+RD={ad+rd:.0f}!=D{d_h:.0f}"
        print(f"\n  {nm[:74]}")
        print(f"    code={code_of(nm) or '-':22}  Duration={d_h:>7.1f} PT-h  = {days:>6.2f} days")
        print(f"    PercentComplete={pct:>3}   ActualDur={ad if ad is not None else '-'}  "
              f"RemainDur={rd if rd is not None else '-'}   {adrd}")
        print(f"    planned Start={t['Start']}  Finish={t['Finish']}   [{sf_flag}]")
        print(f"    ActualStart={t['ActualStart'] or '-'}   ActualFinish={t['ActualFinish'] or '-'}")
        print(f"    -> our-XER hours:  (A) day-for-day x8h = {our_A}h    "
              f"(B) 24/7 footprint on 5d/8h = {our_B}h")
