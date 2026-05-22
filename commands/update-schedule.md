---
description: Apply a schedule update - intake new info, draft a change-set, show the impact preview, stop for approval, then commit.
---

# Schedule Update

Fold a new update into the schedule. Run this whenever an update arrives - a meeting,
a sub-schedule refresh, an email, a decision. It is cadence-neutral: run it daily,
weekly, or several times a day. Work through the phases in order.
**The Approval gate (update phase 4) is a hard STOP - nothing is committed without explicit approval.**

Locations:
- pipeline scripts - `${CLAUDE_PLUGIN_ROOT}/scripts/` (this plugin)
- validators       - `${CLAUDE_PLUGIN_ROOT}/skills/data-center-schedule/scripts/` (bundled skill)
- change-sets   - the project's `changesets/` folder
- schedule XERs - the project's `outputs/` folder
- new inputs    - the project's `inbox/` folder
- lessons log   - the project's `lessons-log.md`

> **Phase numbering.** The phases below are scoped to the **update workflow** only -
> not the same phases as `/build-schedule`, `/harvest-lessons`, or the skill's build
> method. Each section leads with its name; the `update phase N` tag is just ordering.

> **Precondition - the project must be set up first.** `/update-schedule`
> maintains an *existing* schedule project. Before anything else, check the
> connected folder has a `project.yaml` and the `inputs/ outputs/ inbox/
> changesets/` structure. If it does not - an empty or bare folder - the project
> has not been set up: **stop and tell the user to run `/start-project` and choose
> the takeover path.** That scaffolds the folder, places the current schedule XER
> in `outputs/` as the base, and captures the milestones and source hierarchy into
> `project.yaml` - everything this command needs. `/update-schedule` does not
> scaffold; it expects a set-up project.

## Intake · update phase 1
Identify what is new since the last update: meeting minutes, refreshed trade
schedules, equipment-list changes, or direct OPC edits.

> New files for an update go in the project's **`inbox/`** folder. Ask the user to
> drop them there with their **file manager** (File Explorer on Windows, Finder on
> Mac) - **not** by uploading them into the chat. The assistant reads them
> straight from `inbox/`; uploading large schedule files into the conversation
> bloats it and slows everything down.

Read what is in `inbox/`; if unclear, ask which files to process. Establish the
current **base XER** - the latest committed XER, or, if the user edited directly
in OPC, the freshly exported XER (diff it against the last committed XER first, so
the edits are captured). On the first update after `/start-project` set up the
project, the base XER is the one `/start-project` placed in `outputs/`.

## Analysis & draft change-set · update phase 2
Read every new input. Resolve conflicts by the source-of-truth hierarchy in the
project config. Decide the needed schedule changes and write them as a change-set
YAML per docs/changeset-schema.md:
- id: the next CS-NNN in sequence
- base_xer: the current base; update_xer: the next versioned XER
- one operation per change; every operation needs a plain-language reason and a
  source citation (file name, meeting + timestamp, or analysis reference)
- never invent a duration or a logic tie - cite the trade schedule, the equipment
  list, or the contract document it came from
- keep predicted_impact brief; the Impact preview computes the real numbers
- respect the project's scheduling basis (`project.yaml` `scheduling`) - keep
  milestone constraints and actuals consistent with it (see `references/14-scheduling-basis.md`)
Save as changesets/CS-NNN-<slug>.yaml. Write it via the shell (reliable on this folder).

## Impact preview · update phase 3
Run review_changeset.py on the change-set. Show the user the entire Change-Set
Impact Preview - what it changes, the independent verification, the milestone
impact table, the validation comparison, and the verdict.

## Approval gate · update phase 4  --  STOP
Do not proceed. The user must explicitly approve.
- Approved -> Commit.
- Revisions wanted -> edit the change-set YAML, re-run the Impact preview, stop here again.
- If the verdict was REVIEW NEEDED, walk the user through why before they decide.

## Commit · update phase 5
On approval, run apply_changeset.py on the change-set. It stages the update XER,
runs the validators base-relative - blocking only on issue(s) the change-set ADDS,
reporting any pre-existing ones - then commits via an atomic rename, backs up the
base, and appends CHANGELOG.md.

## Hand off · update phase 6
Tell the user to:
1. Import the update XER into OPC - it matches the existing project by Project ID,
   so OPC offers to update the existing project. Accept the update.
2. Run F9 (schedule) in OPC.
3. Export the rescheduled XER - that becomes the base for the next update.
Give a short written summary: what changed, the milestone impact, any flags raised.

## Capture lessons · update phase 7
After the commit, append any lesson candidates from this run to the project's
`lessons-log.md`. Log a candidate when, during this run:
- an input carried bad or self-contradictory logic that had to be flagged
- a source-of-truth conflict had to be resolved
- the user overrode or revised a proposed change at the approval gate
- a duration or logic tie deviated > 1 shift from the trade's stated value
- a validator or duplicate-audit issue surfaced and was corrected
- this change-set reversed or corrected an earlier change-set

Use the entry format in `lessons-log.md` - the next `LL-NNN` in sequence, status
`captured`. Capture is non-blocking: it never gates the schedule, and if there is
nothing to log, skip it. If unsure whether something is a lesson, log it - the
review step filters. Nothing here touches the skill; the log is reviewed later via
`/harvest-lessons`. See `docs/lessons-pipeline.md`.

## Rules
- Never skip the approval gate.
- Never hand-edit an XER - every schedule change goes through a change-set.
- One change-set per run; change-sets are immutable once committed.
- On any failure (bad YAML, expect-mismatch, verification failure), stop and report
  - never produce or hand over a half-applied schedule.
- Capture lessons (update phase 7) is the only step that may run after a failed commit - log the
  failure as a lesson candidate if it revealed something worth keeping.

## Issuing to stakeholders
Applying an update and issuing it to stakeholders are distinct actions - this
command does only the first. Every committed update is logged to `CHANGELOG.md`,
the plugin-side audit trail of what changed. Issuing the weekly stakeholder
package is a separate, manual step done in OPC: once the update is imported and
F9-scheduled, the user publishes the schedule as PDF documents from OPC and sends
those to the GC, subs, and owner. The plugin does not automate that step.
