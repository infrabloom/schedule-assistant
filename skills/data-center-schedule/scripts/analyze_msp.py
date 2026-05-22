"""
analyze_msp.py -- empirically derive the TRUE duration basis of one or more
Microsoft Project XML trade schedules.

  * trust   : Duration, PercentComplete, ActualStart, ActualFinish
  * distrust: planned Start / Finish (trades often don't maintain them)

Method: for COMPLETED activities (ActualStart + ActualFinish + ActualDuration
all present and trustworthy), compute the working-hours between ActualStart and
ActualFinish under several candidate calendar models, and see which model makes
working_hours == ActualDuration. That model IS the basis the durations are in.

Then cross-check:
  * planned Start/Finish vs Duration  -> shows how unreliable the planned dates are
  * Duration vs %complete vs Remaining/ActualDuration -> internal consistency

Usage:
    python analyze_msp.py <msp.xml> [<msp.xml> ...]
    (each argument may be a glob, e.g.  "trade-schedules/*.xml")
"""
import sys, glob, os
from datetime import datetime, timedelta
from parse_msp import load, code_of

# ---- candidate calendar models -------------------------------------------------
# each model: which hours of a day are "working", and which weekdays are working.
# weekday(): Mon=0 .. Sun=6
MODELS = {
    "24x7":      (set(range(24)),            set(range(7))),
    "10h x 7d":  (set(range(6, 16)),         set(range(7))),       # 06-16, every day
    "8h x 7d":   (set(range(8, 16)),         set(range(7))),
    "8h x 6d":   (set(range(8, 16)),         set(range(6))),       # Mon-Sat
    "8h x 5d":   (set(range(8, 16)),         set(range(5))),       # Mon-Fri
    "10h x 5d":  (set(range(6, 16)),         set(range(5))),
    "12h x 7d":  (set(range(6, 18)),         set(range(7))),
}

def working_hours(s, e, model):
    """count working hours between two datetimes under a model (hour resolution)"""
    if s is None or e is None or e <= s:
        return None
    work_hours, work_days = MODELS[model]
    h = 0
    cur = s.replace(minute=0, second=0, microsecond=0)
    end = e
    while cur < end:
        if cur.weekday() in work_days and cur.hour in work_hours:
            # fraction of this hour inside [s,e]
            hr_start = max(cur, s)
            hr_end = min(cur + timedelta(hours=1), end)
            h += (hr_end - hr_start).total_seconds() / 3600.0
        cur += timedelta(hours=1)
    return round(h, 2)

def best_model(s, e, target_h, tol=0.10):
    """which model makes working_hours(s,e) closest to target_h"""
    best, besterr = None, 1e9
    scores = {}
    for m in MODELS:
        wh = working_hours(s, e, m)
        if wh is None:
            continue
        err = abs(wh - target_h) / target_h if target_h else abs(wh)
        scores[m] = (wh, round(err, 3))
        if err < besterr:
            best, besterr = m, err
    return best, besterr, scores

# ---- run ----------------------------------------------------------------------
def main():
    args = sys.argv[1:]
    if not args:
        print("usage: python analyze_msp.py <msp.xml> [<msp.xml> ...]")
        print('       each argument may be a glob, e.g.  "trade-schedules/*.xml"')
        sys.exit(2)
    files = []
    for a in args:
        hits = sorted(glob.glob(a))
        files.extend(hits if hits else [a])
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        print("file(s) not found: " + ", ".join(missing))
        sys.exit(2)

    for path in files:
        name = os.path.basename(path)
        p = load(path)
        real = [t for t in p.tasks if t["Summary"] != "1" and t["Milestone"] != "1"]
        completed = [t for t in real
                     if t["ActualStart_dt"] and t["ActualFinish_dt"]
                     and t["ActualDuration_h"] and t["ActualDuration_h"] > 0]
        print("=" * 78)
        print(f"{name}")
        print(f"  proj MinutesPerDay={p.header['MinutesPerDay']} "
              f"MinutesPerWeek={p.header['MinutesPerWeek']} "
              f"projCal={p.header['CalendarUID']} "
              f"CurrentDate={p.header['CurrentDate']}")
        print(f"  {len(real)} real activities, {len(completed)} completed (trustworthy actuals)")

        # ---- 1. derive the basis from completed activities -------------------
        tally = {}
        rows = []
        for t in completed:
            m, err, scores = best_model(t["ActualStart_dt"], t["ActualFinish_dt"],
                                        t["ActualDuration_h"])
            tally[m] = tally.get(m, 0) + 1
            rows.append((t["Name"][:46], t["ActualDuration_h"], m, err, scores))
        if completed:
            print("  -- basis derived from completed activities "
                  "(working_hrs(ActualStart->ActualFinish) == ActualDuration) --")
            for m, n in sorted(tally.items(), key=lambda kv: -kv[1]):
                print(f"       {m:12} : {n:3} activities")
            # show a few examples
            for nm, ad, m, err, scores in rows[:5]:
                sc = " ".join(f"{k}={v[0]}" for k, v in scores.items())
                print(f"       e.g. {nm:46} ActualDur={ad:7.1f}h -> {m} (err {err:.0%})")

        # ---- 2. planned Start/Finish vs Duration (the unreliable bit) --------
        ns = [t for t in real if t["Start_dt"] and t["Finish_dt"] and t["Duration_h"]]
        matchcnt = {m: 0 for m in MODELS}
        bad = 0
        for t in ns:
            m, err, _ = best_model(t["Start_dt"], t["Finish_dt"], t["Duration_h"])
            if err <= 0.05:
                matchcnt[m] += 1
            else:
                bad += 1
        print(f"  -- planned Start/Finish vs Duration: {len(ns)} testable, "
              f"{bad} do NOT match any calendar model within 5% --")

        # ---- 3. internal consistency: ActualDur + RemainDur vs Duration -----
        inc = 0
        for t in real:
            d, ad, rd = t["Duration_h"], t["ActualDuration_h"], t["RemainingDuration_h"]
            if d and ad is not None and rd is not None:
                if abs((ad + rd) - d) > max(1.0, 0.02 * d):
                    inc += 1
        print(f"  -- internal: ActualDuration + RemainingDuration != Duration on "
              f"{inc} activities --")

if __name__ == "__main__":
    main()
