# Scheduling Basis — Actuals and Milestone Treatment

Every schedule is built on a **scheduling basis**: two independent decisions that
determine how the XER is constructed and how its dates read. They are set in the
build-brief (`scheduling.actuals`, `scheduling.milestones`) and carried in
`project.yaml` for updates. Make them explicit before building — they are not
cosmetic; they change the constraint codes, the actuals, and what the deliverables
mean.

## Background: P6 always runs both passes

On every schedule run (F9), OPC computes:

- a **forward pass** — early dates, working forward from the data date / project
  start through logic + durations. This is the **forecast**: when work *can* happen.
- a **backward pass** — late dates, working back from the project's latest
  required date (or from milestone constraints) through the same logic.
- **total float** = late date − early date. Negative float means the activity
  cannot meet its required date on the current plan.

So "forward pass vs backward pass" is not a choice — both always run. The two
choices that matter are below.

## Axis 1 — `actuals`: is the schedule status-updated?

- **`applied`** — the schedule is **status-updated to the data date**. Completed
  work is `TK_Complete` with `act_start_date` + `act_end_date`; in-progress work
  is `TK_Active` with an `act_start_date`, a `phys_complete_pct`, and a remaining
  duration. OPC schedules all remaining work forward from the **data date**. This
  is a *current / forecast* schedule — it answers "given real progress, where do
  we land?"
- **`none`** — a clean **baseline** plan: every activity `TK_NotStart`, no
  actuals, scheduled forward from a planned start. This is the *target* — what was
  committed before any work began.

Only mark progress with documentary evidence (a trade schedule, a field report) —
never assume an activity is complete or started.

## Axis 2 — `milestones`: are contractual milestones pinned?

- **`to-contract`** — each contractual milestone carries a **`CS_MEOB`** ("finish
  on or before") constraint at its contract date. The backward pass then works
  back from those dates, producing **required dates** and **float to contract**.
  Where the plan cannot meet a contract date, that chain shows **negative float**.
  Use this for an owner-side control schedule: it surfaces slippage and tells you
  what must happen by when. The critical path is the chain driving the milestone
  with the least float.
- **`forecast`** — contractual milestones are **unconstrained**; they fall where
  logic + durations put them. The schedule is a pure forward forecast of when each
  milestone lands; compare the predicted finish to the contract date separately
  (`predict_milestones.py` does exactly this). Use this for an honest "where will
  we actually land" picture, with no constraint masking the slippage.

A milestone constraint is recorded as `cstr_type = CS_MEOB`, `cstr_date = <the
contract date>`. Use **only** the OPC-safe constraint codes — `CS_MEOA`,
`CS_MEOB`, `CS_MSOA` — never bare `CS_MEO` / `CS_MSO`; OPC silently drops those.

## The common combinations

| `actuals` | `milestones` | What the schedule is |
|---|---|---|
| `applied` | `to-contract` | The owner-side **control schedule** — status-updated, shows float / negative float to every contract milestone. The usual choice. |
| `applied` | `forecast` | A **forecast** — honest predicted milestone dates, no constraints; variance vs contract reported separately. |
| `none` | `to-contract` | A **baseline / target** plan — the committed schedule with milestones pinned, before any progress. |
| `none` | `forecast` | A clean logic-only plan — rare; mostly a structural sanity build. |

## How the build uses this

- `actuals: applied` → apply actual start / finish / % complete from the sources
  and set the data date; `none` → every activity `TK_NotStart`.
- `milestones: to-contract` → stamp `CS_MEOB` at each milestone's contract date;
  `forecast` → leave milestones unconstrained.
- The critical-path trace and the deliverables read accordingly — float-to-contract
  under `to-contract`, predicted-vs-contract variance under `forecast`.
