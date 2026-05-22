# Project Config Schema - project.yaml

One `project.yaml` per project (DC1, DC2, ...), in the project folder root. It is
the file that carries project-specific settings - **the plugin code and the
bundled skill never change per project.** `build-brief.yaml` drives a *new build*;
`project.yaml` configures *updates* and the conventions a pipeline run uses.

## Fields

```yaml
project:
  name:        DC1                              # human label
  project_id:  DC1-Draft-V4                     # the OPC Project ID carried in
                                                # every XER - do not change it
  calendar:    "DC1 Standard 7-Day No Holidays" # the schedule's working calendar

paths:                                          # all relative to the project folder
  inbox:       inbox/                           # drop new input files here
  inputs:      inputs/                          # source files
  outputs:     outputs/                         # schedule XER versions + backups
  changesets:  changesets/                      # change-set history (immutable)
  changelog:   CHANGELOG.md                     # the rolled-up audit log
  lessons_log: lessons-log.md                   # captured lesson candidates

milestones:
  contract_pattern: "MS-.*-(EFA|FA|FR|RFS)$|MS-ADMIN-SC$"

source_of_truth:                                # highest authority first
  - "Contractual milestone dates + definitions"
  - "Sub-detailed (electrical / mechanical) schedules + meeting notes"
  - "Locked draft XER - WBS / milestones / site-shell"
  - "Client view XER - reference only"
  - "Historic prior-GC XER - actuals only"

conventions:
  predecessor: "FF for long-lead equipment ties; FS for commodity items"
  constraints: "OPC-safe only - CS_MEOA, CS_MEOB, CS_MSOA"
```

## Who consumes each field

There are two consumers: the **pipeline scripts** (Python) and the **assistant**
(Claude, following the command files).

| Field | Consumed by | How |
|---|---|---|
| `milestones.contract_pattern` | **script** | A regex identifying contract-milestone task codes. `review_changeset.py` auto-discovers `project.yaml` and forwards it to `predict_milestones.py` as `--milestone-pattern`. If the field (or the file) is absent, the script falls back to a generic default. |
| `project.project_id` | reference | The OPC Project ID. The patcher preserves it from `base_xer` unchanged; this field documents the expected value. |
| `project.name` / `project.calendar` | assistant | Context the assistant uses when describing or building the schedule. |
| `paths.*` | assistant | Where the assistant reads inputs and writes outputs in each phase. |
| `source_of_truth` | assistant | The conflict-resolution order to apply when sources disagree. |
| `conventions.*` | assistant | The predecessor / constraint conventions the assistant applies and documents. |

## The milestone pattern - the portability hinge

`contract_pattern` is the one field a **script** reads, and it is what lets the
plugin run on a different client **with no code change**.

`predict_milestones.py` (the milestone CPM pre-check) must know which task codes
are contract milestones. It no longer hardcodes a project-specific regex. Instead:

1. If `review_changeset.py` finds a `project.yaml` with `milestones.contract_pattern`,
   it forwards that exact pattern - the project gets precise milestone detection.
2. If there is no `project.yaml`, `predict_milestones.py` uses a generic default,
   `(?:^|[-_.])(EFA|FA|FR|RFS|MEC|TCO|PCO)(?:[-_.]|$)`, which catches the common
   contract-milestone tokens across data-center projects.

So a new client works out of the box on the generic default, and gets exact
results once its `project.yaml` declares its own naming convention. The pattern is
matched only against activities whose `task_type` is a milestone, so it can be
broad without false positives.

## Adding a new project

To run a second building, create its project folder with the `paths` layout
above, copy this `project.yaml`, and set: `project` (name, `project_id`,
calendar), `milestones.contract_pattern` for that project's milestone codes, and
`source_of_truth`. The plugin and the bundled skill stay untouched - install them
once per device (see `setup-guide.md` and `multi-device-setup.md`).
