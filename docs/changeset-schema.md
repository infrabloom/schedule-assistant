# Change-Set Schema — v1.5

A **change-set** is a YAML file describing one reviewed, approved batch of edits to a single
XER schedule file. It is the contract that runs through the whole pipeline:

- You **review and approve** the change-set — edit it freely before approving.
- The **patcher** (`apply_changeset.py`) applies exactly the operations it contains — nothing else.
- The **verifier** (`diff_xer.py` + the verification agent) confirms the before→after XER diff
  equals this change-set, and flags anything extra.

One change-set = one schedule version step (e.g. V6 → V7). Change-sets are immutable once
applied — they are the audit trail. Each is stored as `changesets/CS-NNN-<slug>.yaml`.

> **Changelog**
> - **v1.1** — `modify_activity` covers name/ID changes; added `split_activity`,
>   `define_activity_code`, `assign_activity_code`, and an inline `codes:` block.
> - **v1.2** — added `remove_activity_code`; added WBS operations `add_wbs` / `modify_wbs`
>   / `remove_wbs`; project version-stamp is now an automatic patcher behavior (§4);
>   added §5 "Out of scope".
> - **v1.3** — after a review of the full original build: added an optional `match:`
>   selector to `modify_relationship` / `remove_relationship` for bulk changes; added a
>   merge/consolidation note (§2.7); made the patcher's OPC-import-safety guarantee
>   explicit (§4); noted replication and source-provenance in §5.
> - **v1.4** — added the optional `requested_by` header field; the patcher now appends
>   each applied change-set to `CHANGELOG.md`, the project change-log archive (§4);
>   renamed the `target_xer` header field to `update_xer` (it carries an update into the
>   one OPC project — it does not replace it).
> - **v1.5** — the patcher now PRESERVES the Project ID (`proj_short_name` + root WBS)
>   unchanged from `base_xer` instead of stamping it with the version. OPC matches an
>   XER import to the existing project by Project ID — stamping it broke update-matching.
>   The version lives in the filename only. Keeps the pipeline project-agnostic.

---

## 1. File structure

A change-set has two top-level keys: `changeset:` (header) and `changes:` (the ordered
list of operations).

```yaml
changeset:
  id: CS-007
  title: "Short human title"
  base_xer: CB4-Draft-V6.xer        # the file this change-set is applied to
  update_xer: CB4-Draft-V7.xer      # the updated XER to import into OPC (an update, not a replacement)
  data_date: 2026-05-15
  prepared: 2026-05-21
  author: "Scheduler (CB4)"
  requested_by: "Patrick"           # optional — who asked for the change
  trigger: "What prompted this batch — meeting, weekly refresh, analysis."
  summary: "Plain-language description of the batch as a whole."
  predicted_impact: { ... }         # optional — see §3

changes:
  - id: C1
    op: modify_relationship
    ...
```

### Header fields

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Change-set id, `CS-NNN`, unique and sequential. |
| `title` | yes | Short human title. |
| `base_xer` | yes | Filename the patch is applied to. Patcher aborts if it can't find it. |
| `update_xer` | yes | Filename the patcher writes — the updated XER to import into the existing OPC project. Never overwrites `base_xer`. |
| `data_date` | yes | Schedule data date — used by the CPM pre-check. |
| `prepared` | yes | Date the change-set was drafted. |
| `author` | yes | Who drafted the change-set. |
| `requested_by` | no | Who requested the change — recorded in `CHANGELOG.md`. |
| `trigger` | yes | What prompted the batch. |
| `summary` | yes | Plain-language description. |
| `predicted_impact` | no | CPM pre-check forecast — see §3. |

---

## 2. Operations

Every entry in `changes:` is one operation. Thirteen types in four groups. Ten
are implemented; the three **activity-code** operations are reserved for a future
increment - the patcher rejects them with a clear error today.

- **Activities** — `add_activity`, `modify_activity`, `split_activity`, `remove_activity`
- **Relationships** — `add_relationship`, `modify_relationship`, `remove_relationship`
- **Activity codes** — `define_activity_code`, `assign_activity_code`, `remove_activity_code`  *(not yet implemented)*
- **WBS** — `add_wbs`, `modify_wbs`, `remove_wbs`

**All operations share four required fields:**

- `id` — unique within the change-set (`C1`, `C2`, …).
- `op` — one of the types above.
- `reason` — why this change, in plain language.
- `source` — the authority for it: file name, meeting + timestamp, or analysis reference.
  **Mandatory and never blank** — an op with no source is rejected.

Most operations also carry `expect:` — the patcher checks the current XER matches `expect`
before applying, and **aborts the whole change-set** if it does not. This catches drift
(the base XER not being what we assumed).

Identifiers: activities by `task_code`; relationships by their `{predecessor, successor}`
task_code pair; WBS nodes by `path`. Relationship types are `FS`, `SS`, `FF`, `SF`; lags
in **working days** (`lag_days`). Constraints use OPC-safe codes only: `MSOA`, `MEOA`,
`MEOB`. See §3.

### 2.1 `modify_relationship`

Target relationships explicitly via `relationships:`, or in bulk via `match:` (glob on
predecessor and successor task_codes). The patcher expands `match:` and records the
resolved list in the run log so the change stays auditable.

```yaml
- id: C1
  op: modify_relationship
  reason: "..."
  source: "..."
  set:       { type: FF, lag_days: 3 }   # new values
  expect:    { type: FS, lag_days: 0 }   # current values — patch aborts on mismatch
  relationships:                          # explicit list ...
    - { predecessor: CONS-DH4-MR-3000, successor: CONS-DH4-MR-2023 }
  # match:   { predecessor: "CONS-DH*-MR-30*", successor: "CONS-DH*-MR-2023" }   # ... or bulk
```

### 2.2 `add_relationship`

```yaml
- id: C2
  op: add_relationship
  reason: "..."
  source: "..."
  relationships:
    - { predecessor: CONS-DH4-DH-2030, successor: CONS-DH4-DH-2035, type: FS, lag_days: 0 }
```

### 2.3 `remove_relationship`

Accepts an explicit `relationships:` list or a bulk `match:` selector (see §2.1).

```yaml
- id: C3
  op: remove_relationship
  reason: "..."
  source: "..."
  expect:  { type: FS, lag_days: 0 }     # optional guard
  relationships:
    - { predecessor: CONS-DH4-MR-2022, successor: CX-DH4-MECH-CHW-1000 }
  # match: { predecessor: "CONS-DH*", successor: "CONS-DH*" }
```

### 2.4 `add_activity`

```yaml
- id: C4
  op: add_activity
  reason: "..."
  source: "..."
  activity:
    code: CONS-DH4-DH-2035
    name: "DH4 - CDU Final Pipe Terminations (6\"-4\" Drop Transition) (MLP)"
    wbs: "04 Construction > Area 4 > Mech Room 4"   # WBS by path
    type: Task                           # Task | Milestone
    calendar: "CB4 Standard 7-Day No Holidays"
    duration_days: 5
    status: NotStarted                   # NotStarted | InProgress | Complete
    actual_start: null
    actual_finish: null
    remain_duration_days: 5
    constraint: null                     # or { type: MEOB, date: 2026-05-25 }
    codes:                               # optional — activity-code assignments (§2.8)
      Trade: Mechanical
      Subcontractor: MLP
  predecessors:
    - { activity: CONS-DH4-DH-2030, type: FS, lag_days: 0 }
  successors:
    - { activity: CONS-DH4-DH-1010, type: FS, lag_days: 0 }
```

### 2.5 `modify_activity`

`set:` may carry **any activity field**: `name`, `wbs`, `calendar`, `type`,
`duration_days`, `remain_duration_days`, `status`, `actual_start`, `actual_finish`,
`target_start`, `target_finish`, `constraint`, and `codes`. Changing the Activity ID
itself is supported via `code:` but is higher-risk — use sparingly.

```yaml
- id: C5
  op: modify_activity
  reason: "..."
  source: "..."
  activity: CONS-DH4-MR-M-FW-PIPE-E
  set:     { name: "DH4 FW Piping East CRAH Gallery (all 12 units, MLP/JWD)" }
  expect:  { name: "DH4 FW Piping East CRAH Gallery (all 15 units, MLP/JWD)" }
```

### 2.6 `split_activity`

Splits one activity into the original (modified) plus a new activity. Mechanically a
`modify_activity` + `add_activity` bundled as one named operation for readability and
audit. It does **not** auto-reassign the original's existing relationships — if ties must
move to the new activity, add explicit `add_relationship` / `remove_relationship` ops.

```yaml
- id: C6
  op: split_activity
  reason: "Fan wall delivery splits 25 units into a batch of 20 and a final 5."
  source: "CB4 schedule review 2026-05-19 (00:23:18)."
  original: PROC-DH4-FCW
  expect:        { name: "DH4 - Fan Coil Walls (25)" }
  modify_original:                       # fields changed on the kept activity
    name: "DH4 - Fan Coil Walls (20)"
  new_activity:                          # full spec — same fields as add_activity
    code: PROC-DH4-FCW10
    name: "DH4 - Fan Coil Walls (5)"
    wbs: "02 Procurement > DH4 Procurement > Mechanical and HVAC Equipment"
    type: Task
    duration_days: 45
    status: InProgress
    remain_duration_days: 24
    codes: { Trade: Mechanical, Subcontractor: MLP }
    predecessors:
      - { activity: MS-PM-1000, type: FS, lag_days: 0 }
    successors: []
```

### 2.7 `remove_activity`

Rare. Requires explicit confirmation in review because it also drops the activity's logic.
A merge of two activities is *not* a single operation — express it as `modify_activity`
on the surviving activity (absorbing scope) + relationship ops + `remove_activity` on the
absorbed one.

**Consolidation caveat:** when merging duplicates (e.g. four per-DH activities into one
site-wide activity), reassign each predecessor and successor *explicitly*. Do not rely on
a blanket retie — the original build's worst logic-cleanup pain came from auto-retie
pulling spurious cross-DH ties off the absorbed copies. The verifier specifically flags
cross-DH relationships introduced by a change-set.

```yaml
- id: C7
  op: remove_activity
  reason: "..."
  source: "..."
  activity: CX-DH4-MECH-CW-1000
  reroute: true        # if true, predecessors are re-tied to successors to avoid orphans
```

### 2.8 `define_activity_code`

> **Not yet implemented.** The patcher rejects `define_activity_code`,
> `assign_activity_code`, `remove_activity_code`, and the `codes:` block on
> activities with a clear error. Sections 2.8–2.10 below are the planned design.

Creates or updates an activity-code **type** and its allowed **values**. An activity code
is a categorization tag (e.g. Trade, Subcontractor, Discipline) used to filter and group —
it is *not* the Activity ID. A value must be defined here before it can be assigned.

```yaml
- id: C8
  op: define_activity_code
  reason: "Introduce subcontractor tagging so the schedule can be filtered by sub."
  source: "..."
  code_type: Subcontractor
  scope: Project                         # Project (recommended) | Global
  values:
    - { code: OCE,  description: "O'Connell Electric" }
    - { code: MLP,  description: "MLP Corp - Mechanical" }
    - { code: FERG, description: "Ferguson Electric" }
    - { code: DAF,  description: "DAF - Cooling Commissioning" }
```

### 2.9 `assign_activity_code`

Assigns a code value to activities — explicit `activities:` list or a `match:` glob on
task_code (the patcher expands `match` and records the resolved list in the run log).

```yaml
- id: C9
  op: assign_activity_code
  reason: "..."
  source: "..."
  code_type: Subcontractor
  assignments:
    - { value: MLP,  activities: [CONS-DH4-MR-2023, CONS-DH4-MR-2024] }
    - { value: OCE,  match: "CONS-DH*-MR-11*" }
```

An activity may hold one value per code type and several code types at once
(e.g. `Trade: Electrical` **and** `Subcontractor: OCE`).

### 2.10 `remove_activity_code`

Removes activity-code data — two cases, distinguished by the fields supplied.

```yaml
# Case A — untag activities (the value and type stay in the dictionary):
- id: C10
  op: remove_activity_code
  reason: "..."
  source: "..."
  code_type: Subcontractor
  activities: [CONS-DH4-MR-2023]         # or  match: "pattern"

# Case B — delete values, or a whole type, from the dictionary
#          (this also clears any assignments that used them):
- id: C11
  op: remove_activity_code
  reason: "..."
  source: "..."
  code_type: Subcontractor
  values: [TBD]                          # omit `values:` to delete the entire code type
```

### 2.11 `add_wbs`

```yaml
- id: C12
  op: add_wbs
  reason: "..."
  source: "..."
  wbs:
    parent: "04 Construction > Area 4"   # parent WBS by path
    code: "MR4-CX"
    name: "Mech Room 4 - Commissioning"
```

### 2.12 `modify_wbs`

Renames, renumbers, or reparents a WBS node. Identify the node by its current `path`.

```yaml
- id: C13
  op: modify_wbs
  reason: "..."
  source: "..."
  wbs: "03 Procurement"                  # current path
  set:    { code: "02", name: "02 Procurement" }
  expect: { code: "03", name: "03 Procurement" }
  # set: may also carry  parent: "<new parent path>"  to reparent
```

### 2.13 `remove_wbs`

```yaml
- id: C14
  op: remove_wbs
  reason: "..."
  source: "..."
  wbs: "07 Closeout > DH4 Closeout"      # must contain no activities or child nodes
```

---

## 3. Identifiers

- **Activity ID** (`task_code`, e.g. `CONS-DH4-MR-2023`) — the unique activity identifier.
  Changed only via `modify_activity` `code:`, rarely.
- **Activity Code** — a categorization tag (Trade, Subcontractor, …) assigned to activities
  for filtering/grouping. Managed by the `*_activity_code` operations.
- **Relationships** — identified by their `{predecessor, successor}` task_code pair.
- **WBS nodes** — identified by `path` (parent chain of names, ` > ` separated).
- Relationship types: `FS`, `SS`, `FF`, `SF`. Lags in **working days**.
- Constraints — OPC-safe codes only: `MSOA`, `MEOA`, `MEOB`.

---

## 4. Rules enforced by the pipeline

1. Every operation must have a non-empty `source`.
2. Any `expect` mismatch aborts the entire change-set — no partial application.
3. An `assign_activity_code` value must already exist (defined in this or an earlier change-set).
4. `remove_wbs` is rejected if the node still holds activities or child nodes.
5. The patcher always writes a timestamped backup of `base_xer` before producing `update_xer`.
6. The patcher **preserves** `proj_short_name` and the root WBS node (the Project ID)
   unchanged from `base_xer`. OPC matches an import to the existing project by this
   Project ID, so it must stay constant — the version is carried by the filename only.
7. The patcher builds OPC-import-safe rows by construction — new TASK rows are cloned from
   a template (never built field-by-field), `duration_type` matches `task_type`, timestamps
   use 08:00 / 16:00 (never midnight), GUIDs are standard base64, task_codes are
   case-insensitively unique, and `proj_id` is consistent. `validate_xer.py` confirms it.
8. After patching, `validate_xer.py` and `duplicate_audit.py` run against both
   `base_xer` and the staged update. The gate is base-relative: only issue(s) the
   change-set **adds** (new orphans, cycles, duplicates, OPC-unsafe constraints)
   block it. Issues carried over from `base_xer` are reported, not blocked.
9. The verifier diffs `base_xer` vs `update_xer` and confirms the diff equals this
   change-set exactly — any unexplained delta is flagged.
10. On success the patcher appends the change-set to `CHANGELOG.md` — the rolled-up
    historical archive of every change across the project lifecycle.
11. `update_xer` is import-ready but **not yet scheduled** — OPC must run F9 on import.

---

## 5. Out of scope / noted (v1.3)

The working CB4 files do not currently use these, so the schema does not yet cover them.
Operations will be added when first needed:

- **Resource loading** — `RSRC` / `TASKRSRC` tables (no resources in the current schedule).
- **User-defined fields** — `UDFTYPE` / `UDFVALUE`.
- **New calendars** — `modify_activity` can assign an *existing* calendar, but creating a
  new calendar type is not yet supported (the project uses one 7-day calendar).

Noted but intentionally not given a dedicated operation:

- **Replication** — copying a structure across the four Data Halls with an N-day stagger
  is a recurring pattern, but it is just bulk `add_activity`. A `replicate` convenience
  operation may be added later; it is not required.
- **Per-activity source provenance** — which OCE/MLP leaf an activity came from is held in
  the change-set audit trail (the `source` field on every `add_activity`), not embedded in
  the XER. Embedding it in-schedule would require a UDF (see above).
