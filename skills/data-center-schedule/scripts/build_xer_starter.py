"""
build_xer_starter.py — XER generator skeleton for a new DC schedule project.

>>> SKELETON / TEST USE ONLY <<<
This script WRITES XER ROWS FROM SCRATCH. That is fine for a minimal viable
test XER, but a PRODUCTION build must NOT do this -- OPC silently drops
from-scratch rows (a real project lost 389 activities that way). For a real
build, clone
a real TASK row from a known-good template XER as the schema baseline and
overwrite only the fields you control. See references/06-lessons-learned.md
lesson #38, and references/10-acceptance-criteria.md.

Copy this file to outputs/build_xer_v1.py in your new project. Edit:
  - PROJECT_CODE, PROJECT_NAME, DATA_DATE, CALENDAR_ID
  - WBS_HIERARCHY (Level 1-4)
  - T() calls — every activity
  - P() calls — every predecessor tie
  - TASK_CONSTRAINTS — every constrained milestone

Run: python build_xer_v1.py
Output: outputs/{PROJECT_CODE}-Schedule-v1.xer

Then validate: python validate_xer.py outputs/{PROJECT_CODE}-Schedule-v1.xer
"""

import base64
import datetime as dt
import uuid
from collections import namedtuple
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ============================================================
# PROJECT METADATA — edit these for your project
# ============================================================

PROJECT_CODE = "DC1"  # 2-4 chars, used in filenames
PROJECT_NAME = "Hyperscale DC Build"
DATA_DATE = dt.datetime(2026, 5, 8, 17)  # snapshot of project state
CALENDAR_ID = "CAL-5DAY"
PROJ_ID = 1  # internal P6 project ID — keep at 1 unless multi-project XER
OUTPUT_PATH = Path(__file__).parent / f"{PROJECT_CODE}-Schedule-v1.xer"

CONTRACTUAL = {
    # milestone code: (date, constraint type)
    # CS_MEOA = Finish On or After (floor)
    # CS_MEOB = Finish On or Before / FNL (ceiling)
    # CS_MSOA = Start On or After / SNE
    # NEVER use CS_MEO or CS_MSO — OPC silently drops them
    "MS-EFA-DH4": (dt.datetime(2026, 6, 15, 17), "CS_MEOB"),
    "MS-FA-DH4":  (dt.datetime(2026, 7, 31, 17), "CS_MEOB"),
    "MS-EFA-DH3": (dt.datetime(2026, 7, 6, 17),  "CS_MEOB"),
    "MS-FA-DH3":  (dt.datetime(2026, 9, 14, 17), "CS_MEOB"),
    "MS-EFA-DH2": (dt.datetime(2026, 7, 27, 17), "CS_MEOB"),
    "MS-FA-DH2":  (dt.datetime(2026, 10, 29, 17),"CS_MEOB"),
    "MS-EFA-DH1": (dt.datetime(2026, 8, 17, 17), "CS_MEOB"),
    "MS-FA-DH1":  (dt.datetime(2026, 12, 13, 17),"CS_MEOB"),
}


# ============================================================
# WBS HIERARCHY — edit Level 1-4 for your project
# ============================================================

WBS_HIERARCHY = [
    # (code, parent_code_or_None, name)
    (PROJECT_CODE, None, PROJECT_NAME),
    # Level 1 branches
    (f"{PROJECT_CODE}.01", PROJECT_CODE, "01 Milestones"),
    (f"{PROJECT_CODE}.02", PROJECT_CODE, "02 Procurement"),
    (f"{PROJECT_CODE}.03", PROJECT_CODE, "03 Site & Shell"),
    (f"{PROJECT_CODE}.04", PROJECT_CODE, "04 Construction"),
    (f"{PROJECT_CODE}.05", PROJECT_CODE, "05 Final Inspections"),
    (f"{PROJECT_CODE}.06", PROJECT_CODE, "06 Commissioning"),
    (f"{PROJECT_CODE}.07", PROJECT_CODE, "07 Closeout"),
    # Level 2 — per-DH under Construction
    (f"{PROJECT_CODE}.04.DH4", f"{PROJECT_CODE}.04", "DH4 (Area 4)"),
    (f"{PROJECT_CODE}.04.DH3", f"{PROJECT_CODE}.04", "DH3 (Area 3)"),
    (f"{PROJECT_CODE}.04.DH2", f"{PROJECT_CODE}.04", "DH2 (Area 2)"),
    (f"{PROJECT_CODE}.04.DH1", f"{PROJECT_CODE}.04", "DH1 (Area 1)"),
    (f"{PROJECT_CODE}.04.ADMIN", f"{PROJECT_CODE}.04", "Admin Building"),
    # Level 3 — per-DH room split (example for DH4)
    (f"{PROJECT_CODE}.04.DH4.MR", f"{PROJECT_CODE}.04.DH4", "DH4 Mech Room"),
    (f"{PROJECT_CODE}.04.DH4.DH", f"{PROJECT_CODE}.04.DH4", "DH4 Data Hall"),
    (f"{PROJECT_CODE}.04.DH4.YN", f"{PROJECT_CODE}.04.DH4", "DH4 Yard East"),
    (f"{PROJECT_CODE}.04.DH4.YS", f"{PROJECT_CODE}.04.DH4", "DH4 Yard West"),
    (f"{PROJECT_CODE}.04.DH4.RF", f"{PROJECT_CODE}.04.DH4", "DH4 Roof"),
    # ... (replicate for DH3, DH2, DH1)
    # Level 2 — Commissioning per-DH
    (f"{PROJECT_CODE}.06.DH4", f"{PROJECT_CODE}.06", "DH4 Commissioning"),
    (f"{PROJECT_CODE}.06.DH3", f"{PROJECT_CODE}.06", "DH3 Commissioning"),
    (f"{PROJECT_CODE}.06.DH2", f"{PROJECT_CODE}.06", "DH2 Commissioning"),
    (f"{PROJECT_CODE}.06.DH1", f"{PROJECT_CODE}.06", "DH1 Commissioning"),
]


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Task:
    code: str           # activity ID, e.g. "CONS-DH4-MR-1000"
    name: str
    duration_hr: int    # target_drtn_hr_cnt
    wbs: str            # parent WBS code
    task_type: str = "TT_Task"  # TT_Task | TT_Mile | TT_FinMile
    status: str = "TK_NotStart"  # TK_NotStart | TK_Active | TK_Complete
    act_start: Optional[dt.datetime] = None
    act_end: Optional[dt.datetime] = None
    phys_pct: float = 0.0
    calendar: str = CALENDAR_ID
    guid: str = field(default_factory=lambda: base64.b64encode(uuid.uuid4().bytes).decode("ascii").rstrip("="))


@dataclass
class Pred:
    succ: str           # successor activity code
    pred: str           # predecessor activity code
    ptype: str = "PR_FS"  # PR_FS | PR_SS | PR_FF (NEVER PR_SF)
    lag_hr: int = 0


tasks: list[Task] = []
preds: list[Pred] = []
TASK_CONSTRAINTS: dict[str, tuple[dt.datetime, str]] = {}


def T(code, name, duration_hr, wbs, **kwargs):
    """Shortcut to create + register a task."""
    t = Task(code=code, name=name, duration_hr=duration_hr, wbs=wbs, **kwargs)
    tasks.append(t)
    return t


def P(succ, pred, ptype="PR_FS", lag_hr=0):
    """Shortcut to create + register a predecessor tie."""
    # accept Task objects or codes
    succ_code = succ.code if isinstance(succ, Task) else succ
    pred_code = pred.code if isinstance(pred, Task) else pred
    p = Pred(succ=succ_code, pred=pred_code, ptype=ptype, lag_hr=lag_hr)
    preds.append(p)
    return p


# ============================================================
# ACTIVITIES — add yours here
# ============================================================

# Example: Milestones
T("MS-AFEED", "AFEED Live (A-Feed Utility)", 0,
  wbs=f"{PROJECT_CODE}.01", task_type="TT_FinMile")
T("MS-BFEED", "BFEED Live (B-Feed Utility)", 0,
  wbs=f"{PROJECT_CODE}.01", task_type="TT_FinMile")
TASK_CONSTRAINTS["MS-AFEED"] = (dt.datetime(2026, 6, 22, 17), "CS_MEOA")
TASK_CONSTRAINTS["MS-BFEED"] = (dt.datetime(2026, 12, 15, 17), "CS_MEOA")

# Contractual milestones
for code, (date, cstr) in CONTRACTUAL.items():
    dh = code.split("-")[-1]  # DH1..DH4
    T(code, f"{code.replace('MS-','').replace('-',' ')} Contract Milestone", 0,
      wbs=f"{PROJECT_CODE}.01", task_type="TT_FinMile")
    TASK_CONSTRAINTS[code] = (date, cstr)


# Example: a single Mech Room activity
T("CONS-DH4-MR-1000", "DH4 MR MV Switchgear Set", 40,
  wbs=f"{PROJECT_CODE}.04.DH4.MR")
T("CONS-DH4-MR-1190", "DH4 Mech Room Ready (Electrical)", 40,
  wbs=f"{PROJECT_CODE}.04.DH4.MR")

# Example: a commissioning activity
T("CX-DH4-L3-MV-EN", "DH4 L3 MV Energization", 40,
  wbs=f"{PROJECT_CODE}.06.DH4")

# Example: predecessor ties
P("CONS-DH4-MR-1190", "CONS-DH4-MR-1000")
P("CX-DH4-L3-MV-EN", "CONS-DH4-MR-1190")
P("MS-EFA-DH4", "CX-DH4-L3-MV-EN", ptype="PR_FF")


# ============================================================
# Replicate this pattern for every Area and every activity
# See 03-Schedule-Patterns.md § 2 for the full per-DH catalog
# ============================================================


# ============================================================
# XER WRITER
# ============================================================

def fmt_date(d: Optional[dt.datetime]) -> str:
    return d.strftime("%Y-%m-%d %H:%M") if d else ""


def write_xer(path: Path):
    """Write a minimal P6 XER file with the data above.

    NOTE: This is a SKELETON — a real XER has 18 tables (CURRTYPE, FINDATES,
    PCATTYPE, PCATVAL, OBS, ROLES, USERS, ACCOUNTS, ROLERATE, RSRC, etc.).
    For a full implementation, use a template XER as the structural baseline
    and only re-emit TASK, TASKPRED, PROJWBS, PROJECT, CALENDAR rows.

    The proven approach: load a template XER, replace PROJECT/PROJWBS/TASK/TASKPRED
    sections, keep everything else from the template.
    """
    lines = []
    lines.append("ERMHDR\t20.12\t" + DATA_DATE.strftime("%Y-%m-%d") + "\tProject\tNotEnabled\t\t\tUSD\t1\t6\t1")

    # PROJECT
    lines.append("%T\tPROJECT")
    lines.append("%F\tproj_id\tfy_start_month_num\trsrc_self_add_flag\tallow_complete_flag\trsrc_multi_assign_flag\tcheckout_flag\tproject_flag\tstep_complete_flag\tcost_qty_recalc_flag\tbatch_sum_flag\tname_sep_char\tdef_complete_pct_type\tproj_short_name\tacct_id\torig_proj_id\tsource_proj_id\tbase_type_id\tclndr_id\tsum_base_proj_id\ttask_code_base\ttask_code_step\tpriority_num\twbs_max_sum_level\tstrgy_priority_num\tlast_checksum\tcritical_drtn_hr_cnt\tdef_cost_per_qty\tlast_recalc_date\tplan_start_date\tplan_end_date\tscd_end_date\tadd_date\tlast_tasksum_date\tfcst_start_date\tdef_duration_type\ttask_code_prefix\tguid\tdef_qty_type\tadd_by_name\twbs_pred_delay_type\tplan_type\tlast_baseline_update_date\tcr_external_key\tapply_actuals_date\tlast_fin_dates_id\tlast_baseline_update_date_pi\tcross_prj_link_flag\tname\ttask_code_prefix_flag\tdef_rollup_cstr\trate_type")
    lines.append(f"%R\t{PROJ_ID}\t1\tN\tY\tN\tN\tY\tN\tN\tN\t.\tCP_Drtn\t{PROJECT_CODE}\t\t\t\t\t{CALENDAR_ID}\t\t1000\t10\t10\t1\t10\t0\t0\t0\t{fmt_date(DATA_DATE)}\t{fmt_date(DATA_DATE)}\t\t\t{fmt_date(DATA_DATE)}\t\t\tDT_FixedDUR2\t\t{base64.b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=')}\tQT_Labor\t\tWD_Early\tPT_Cost\t\t\t{fmt_date(DATA_DATE)}\t\t\tN\t{PROJECT_NAME}\tN\tCstr_Both\tDP_Cur")

    # CALENDAR
    lines.append("%T\tCALENDAR")
    lines.append("%F\tclndr_id\tdefault_flag\tclndr_name\tproj_id\tbase_clndr_id\tlast_chng_date\tclndr_type\tday_hr_cnt\tweek_hr_cnt\tmonth_hr_cnt\tyear_hr_cnt\trsrc_private\tclndr_data")
    lines.append(f"%R\t{CALENDAR_ID}\tY\t5-Day Standard\t{PROJ_ID}\t\t\tCA_Base\t8\t40\t172\t2000\tN\t(0||CalendarData()(0||DaysOfWeek()(0||1()(0||0(s|08:00|f|17:00)())(0||2()(0||0(s|08:00|f|17:00)())(0||3()(0||0(s|08:00|f|17:00)())(0||4()(0||0(s|08:00|f|17:00)())(0||5()(0||0(s|08:00|f|17:00)())(0||6()())(0||7()()))()))")

    # PROJWBS
    lines.append("%T\tPROJWBS")
    lines.append("%F\twbs_id\tproj_id\tobs_id\tseq_num\test_wt\tproj_node_flag\tsum_data_flag\tstatus_code\twbs_short_name\twbs_name\tphase_id\tparent_wbs_id\tev_user_pct\tev_etc_user_value\torig_cost\tindep_remain_total_cost\tann_dscnt_rate_pct\tdscnt_period_type\tindep_remain_work_qty\tanticip_start_date\tanticip_end_date\test_wt_method_id\tguid\ttmpl_guid")
    wbs_id_map = {}
    next_wbs_id = 1000
    for code, parent, name in WBS_HIERARCHY:
        wbs_id_map[code] = next_wbs_id
        parent_id = wbs_id_map.get(parent, "") if parent else ""
        is_proj_node = "Y" if parent is None else "N"
        lines.append(f"%R\t{next_wbs_id}\t{PROJ_ID}\t\t10\t1\t{is_proj_node}\tN\tWS_Open\t{code}\t{name}\t\t{parent_id}\t0\t0\t0\t0\t0\tDP_Cur\t0\t\t\t\t{base64.b64encode(uuid.uuid4().bytes).decode('ascii').rstrip('=')}\t")
        next_wbs_id += 1

    # TASK
    lines.append("%T\tTASK")
    lines.append("%F\ttask_id\tproj_id\twbs_id\tclndr_id\tphys_complete_pct\trev_fdbk_flag\test_wt\tlock_plan_flag\tauto_compute_act_flag\tcomplete_pct_type\ttask_type\tduration_type\tstatus_code\ttask_code\ttask_name\trsrc_id\ttotal_float_hr_cnt\tfree_float_hr_cnt\tremain_drtn_hr_cnt\tact_work_qty\tremain_work_qty\ttarget_work_qty\ttarget_drtn_hr_cnt\tact_equip_qty\tremain_equip_qty\ttarget_equip_qty\tcstr_date\tact_start_date\tact_end_date\tlate_start_date\tlate_end_date\texpect_end_date\tearly_start_date\tearly_end_date\trestart_date\treend_date\ttarget_start_date\ttarget_end_date\trem_late_start_date\trem_late_end_date\tcstr_type\tpriority_type\tsuspend_date\tresume_date\tfloat_path\tfloat_path_order\tguid\ttmpl_guid\tcstr_date2\tcstr_type2\tdriving_path_flag\tact_this_per_work_qty\tact_this_per_equip_qty\texternal_early_start_date\texternal_late_end_date\tcreate_date\tupdate_date\tcreate_user\tupdate_user\tlocation_id")
    task_id_map = {}
    next_task_id = 100000
    for t in tasks:
        task_id_map[t.code] = next_task_id
        wbs_id = wbs_id_map.get(t.wbs, "")
        dur_type = "DT_FixedDrtn" if t.task_type in ("TT_Mile", "TT_FinMile") else "DT_FixedDUR2"
        cstr_date, cstr_type = "", ""
        if t.code in TASK_CONSTRAINTS:
            cd, ct = TASK_CONSTRAINTS[t.code]
            cstr_date = fmt_date(cd)
            cstr_type = ct
        remain = 0 if t.status == "TK_Complete" else t.duration_hr * (1 - t.phys_pct / 100)
        act_start = fmt_date(t.act_start)
        act_end = fmt_date(t.act_end)
        lines.append(f"%R\t{next_task_id}\t{PROJ_ID}\t{wbs_id}\t{t.calendar}\t{t.phys_pct}\tN\t1\tN\tN\tCP_Drtn\t{t.task_type}\t{dur_type}\t{t.status}\t{t.code}\t{t.name}\t\t0\t0\t{int(remain)}\t0\t0\t0\t{t.duration_hr}\t0\t0\t0\t{cstr_date}\t{act_start}\t{act_end}\t\t\t\t\t\t\t\t\t\t\t\t{cstr_type}\tPT_Normal\t\t\t\t0\t{t.guid}\t\t\t\tN\t0\t0\t\t\t{fmt_date(DATA_DATE)}\t{fmt_date(DATA_DATE)}\tadmin\tadmin\t")
        next_task_id += 1

    # TASKPRED
    lines.append("%T\tTASKPRED")
    lines.append("%F\ttask_pred_id\ttask_id\tpred_task_id\tproj_id\tpred_proj_id\tpred_type\tlag_hr_cnt\tcomments\tfloat_path\taref\tarls")
    next_pred_id = 200000
    for p in preds:
        succ_id = task_id_map.get(p.succ)
        pred_id = task_id_map.get(p.pred)
        if not succ_id or not pred_id:
            print(f"WARN: skipping orphan tie {p.succ} <- {p.pred} (missing task)")
            continue
        lines.append(f"%R\t{next_pred_id}\t{succ_id}\t{pred_id}\t{PROJ_ID}\t{PROJ_ID}\t{p.ptype}\t{p.lag_hr}\t\t\t{fmt_date(DATA_DATE)}\t{fmt_date(DATA_DATE)}")
        next_pred_id += 1

    lines.append("%E")

    path.write_text("\n".join(lines), encoding="cp1252")
    print(f"Wrote {path} ({len(tasks)} tasks, {len(preds)} preds)")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    write_xer(OUTPUT_PATH)
    print()
    print("Next steps:")
    print(f"  1. Validate: python validate_xer.py {OUTPUT_PATH}")
    print(f"  2. Import to OPC and verify scheduling succeeds")
    print(f"  3. Check forecasted milestone dates vs contractual")
