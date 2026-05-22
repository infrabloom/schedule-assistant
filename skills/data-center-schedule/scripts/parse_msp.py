"""
parse_msp.py -- parser for Microsoft Project XML schedules (OCE + MLP source files).

MSP XML facts that matter here:
  - namespace http://schemas.microsoft.com/project
  - <Task> has DIRECT children for the live values (Duration, Start, Finish,
    ActualStart, ActualFinish, ActualDuration, RemainingDuration, Percent*...)
  - a <Task> can also contain a nested <Baseline> with its OWN Start/Finish/
    Duration, and many <TimephasedData> blocks with their own Start/Finish.
    We must read DIRECT children only so we don't pick those up.
  - <Duration> etc. are ISO-8601 durations: PT<h>H<m>M<s>S
  - <Calendar> defines working time; project header has MinutesPerDay/Week.

Usage:  from parse_msp import load ;  proj = load(path)
        proj.header  -> dict of project-level fields
        proj.tasks   -> list of dicts (one per Task, direct-child fields only)
        proj.cals    -> dict uid -> calendar dict (hours/day, days/week, name)
"""
import re
import xml.etree.ElementTree as ET
from datetime import datetime

NS = "{http://schemas.microsoft.com/project}"


def _iso_dur_to_hours(s):
    """'PT280H0M0S' -> 280.0 ; '' / None -> None"""
    if not s:
        return None
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s.strip())
    if not m:
        return None
    h = int(m.group(1) or 0)
    mn = int(m.group(2) or 0)
    sec = int(m.group(3) or 0)
    return round(h + mn / 60.0 + sec / 3600.0, 4)


def _dt(s):
    if not s:
        return None
    try:
        return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def _txt(el, tag):
    """direct-child text only"""
    c = el.find(NS + tag)
    return c.text if c is not None and c.text is not None else ""


class Proj:
    def __init__(self, header, tasks, cals):
        self.header = header
        self.tasks = tasks
        self.cals = cals


def _parse_calendars(root):
    cals = {}
    cnode = root.find(NS + "Calendars")
    if cnode is None:
        return cals
    for c in cnode.findall(NS + "Calendar"):
        uid = _txt(c, "UID")
        name = _txt(c, "Name")
        base = _txt(c, "BaseCalendarUID")
        wds = c.find(NS + "WeekDays")
        working_days = 0
        day_hours = []
        if wds is not None:
            for w in wds.findall(NS + "WeekDay"):
                dtype = _txt(w, "DayType")          # 1-7 = Sun-Sat, 0 = exception
                dworking = _txt(w, "DayWorking")
                if dtype and dtype != "0":
                    if dworking == "1":
                        working_days += 1
                        # sum working time for this day
                        wt = w.find(NS + "WorkingTimes")
                        hrs = 0.0
                        if wt is not None:
                            for t in wt.findall(NS + "WorkingTime"):
                                ft = _txt(t, "FromTime")
                                tt = _txt(t, "ToTime")
                                if ft and tt:
                                    fh = _dt("2000-01-01T" + ft)
                                    th = _dt("2000-01-01T" + tt)
                                    if fh and th:
                                        d = (th - fh).total_seconds() / 3600.0
                                        if d <= 0:
                                            d += 24   # 00:00->00:00 = 24h (MSP)
                                        hrs += d
                        day_hours.append(hrs)
        hpd = round(sum(day_hours) / len(day_hours), 2) if day_hours else 0.0
        cals[uid] = {
            "uid": uid, "name": name, "base": base,
            "working_days_per_week": working_days,
            "hours_per_working_day": hpd,
            "hours_per_week": round(hpd * working_days, 2),
        }
    return cals


TASK_FIELDS = [
    "UID", "ID", "Name", "WBS", "OutlineNumber", "OutlineLevel",
    "Duration", "Start", "Finish",
    "ActualStart", "ActualFinish", "ActualDuration", "RemainingDuration",
    "PercentComplete", "PercentWorkComplete", "PhysicalPercentComplete",
    "Milestone", "Summary", "Active", "Manual", "CalendarUID",
    "ConstraintType", "ConstraintDate", "Work", "ActualWork", "RemainingWork",
]
DUR_FIELDS = {"Duration", "ActualDuration", "RemainingDuration",
              "Work", "ActualWork", "RemainingWork"}


def load(path):
    tree = ET.parse(path)
    root = tree.getroot()
    header = {}
    for k in ("Name", "Title", "Author", "CreationDate", "LastSaved",
              "StartDate", "FinishDate", "CurrentDate", "StatusDate",
              "CalendarUID", "MinutesPerDay", "MinutesPerWeek", "DaysPerMonth",
              "DefaultStartTime", "DefaultFinishTime", "ScheduleFromStart"):
        header[k] = _txt(root, k)
    cals = _parse_calendars(root)

    tasks = []
    tnode = root.find(NS + "Tasks")
    if tnode is not None:
        for t in tnode.findall(NS + "Task"):
            rec = {}
            for f in TASK_FIELDS:
                v = _txt(t, f)
                if f in DUR_FIELDS:
                    rec[f + "_h"] = _iso_dur_to_hours(v)
                    rec[f + "_raw"] = v
                else:
                    rec[f] = v
            # convenience parsed datetimes
            for f in ("Start", "Finish", "ActualStart", "ActualFinish"):
                rec[f + "_dt"] = _dt(rec.get(f, ""))
            tasks.append(rec)
    return Proj(header, tasks, cals)


# extract a CB4-style activity code from the Name, e.g. "(CB4.CONS.OCE.3200)"
_CODE = re.compile(r"\(([A-Za-z0-9.\-/ ]+)\)\s*$")


def code_of(name):
    m = _CODE.search(name or "")
    return m.group(1).strip() if m else ""


if __name__ == "__main__":
    import sys
    p = load(sys.argv[1])
    print("HEADER:")
    for k, v in p.header.items():
        print(f"  {k:20}= {v}")
    print(f"\nCALENDARS ({len(p.cals)}):")
    for uid, c in p.cals.items():
        print(f"  UID {uid:>4}  {c['name'][:34]:34}  "
              f"{c['working_days_per_week']}d/wk  "
              f"{c['hours_per_working_day']}h/day  "
              f"{c['hours_per_week']}h/wk  base={c['base']}")
    real = [t for t in p.tasks if t["Summary"] != "1" and t["Milestone"] != "1"]
    print(f"\nTASKS: {len(p.tasks)} total, "
          f"{sum(1 for t in p.tasks if t['Summary']=='1')} summary, "
          f"{sum(1 for t in p.tasks if t['Milestone']=='1')} milestone, "
          f"{len(real)} real activities")
