# Build-Brief Schema - the contract for /build-schedule

A **build-brief** (`build-brief.yaml`, one per project) tells `/build-schedule`
what to build. It is to a build what a change-set is to an update: the single
declarative input. The assistant drafts it with you in the Brief & classify phase;
you approve it at that checkpoint. Copy `build-brief.example.yaml` to the project folder
as `build-brief.yaml` and fill it in.

## Fields

```yaml
project:
  id:         CB5                      # short code, used in filenames
  name:       CB5 Hyperscale DC Build
  owner:      OWNER                    # the entity the schedule belongs to
  gc:         GC                       # general contractor
  data_date:  2026-06-01               # the "now" line for the build
  calendar:   7d-8h                    # working pattern: 5d / 6d / 7d, hours/day

detail_level: 3                        # target schedule level 1-5 (skill ref 09)
                                       # 1 milestone | 2 summary | 3 control CPM
                                       # 4 execution | 5 look-ahead
mode:         full-input               # full-input | minimal-input
template:     VA2-DC                   # closest bundled P6 template (skill ref 12)

units:                                 # the repeating spatial-temporal unit
  type:          Data Hall             # Data Hall / Phase / Unit - owner-specific
  count:         4
  sequence:      [DH4, DH3, DH2, DH1]  # build order
  stagger_weeks: 3                     # offset between consecutive units

milestones:                            # contractual milestones (per unit)
  - {code: EFA, name: Early First Access, definition: "...", date: 2026-09-15}
  - {code: FA,  name: Facility Access,    definition: "...", date: 2026-11-30}
  - {code: FR,  name: Facility Ready,     definition: "...", date: 2027-01-31}
  - {code: RFS, name: Ready For Service,  definition: "...", date: 2027-02-28}

inputs:                                # every file in inputs/, role-tagged
  - {file: prior-GC-schedule.xer, role: bad-schedule}    # actuals only
  - {file: OCE-electrical.xml,    role: trade-schedule}
  - {file: MLP-mechanical.xml,    role: trade-schedule}
  - {file: equipment-list.csv,    role: mel}
  - {file: turnover-dates.pdf,    role: client-context}

source_of_truth:                       # conflict resolution, highest authority first
  - client-context
  - trade-schedule
  - good-schedule
  - template
  - bad-schedule                       # actuals only

notes: |
  Free text - anything the builder must know up front.
```

## Role tags (the good- / bad-schedule distinction)

- `template` - a P6 reference XER: copy STRUCTURE only, never import as a baseline.
- `client-context` - milestone definitions and contract dates: highest authority.
- `good-schedule` - a sound prior schedule: import logic + durations + actuals.
- `bad-schedule` - a flawed prior schedule: mine for ACTUALS ONLY; never its logic.
- `trade-schedule` - a sub's detailed schedule: source of truth for that
  discipline's logic, durations, and progress.
- `mel` - Master Equipment List: source of truth for procurement.

## Minimal-input mode

When `mode: minimal-input`, the `inputs` list is empty or just a description.
The builder scaffolds from the bundled skill - the closest P6 template, the
activity catalog (ref 13), the duration benchmarks (ref 08), the patterns
(ref 02). Set `template` to the closest match and `detail_level` to the target.
Every value the builder produces is pattern-derived: it must all land in the
assumptions register, flagged for trade confirmation. A minimal-input build is
delivered as a clearly-marked DRAFT.

## Detail level

`detail_level` selects schedule density per `references/09-schedule-levels.md`.
L3 is the usual owner-side control schedule. L1 / L2 are summary roll-ups;
L4 / L5 explode each L3 activity into work packages / daily tasks and need
crew-level trade data - absent that, the builder emits a flagged shell.
