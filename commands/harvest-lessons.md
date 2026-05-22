---
description: Review the project's lessons-log, propose which lessons to promote into the bundled data-center-schedule skill, stop for approval, then promote.
---

# Harvest Lessons

Turn the lessons captured during day-to-day work into durable improvements to the
bundled `data-center-schedule` skill. Run this at a project wrap-up, at a phase
boundary, or any time the lessons-log has built up. It is the review-and-promote
half of the lessons pipeline; `/build-schedule` and `/update-schedule` are the
capture half. See `docs/lessons-pipeline.md` for the full model.
**The Approval gate (harvest phase 4) is a hard STOP - nothing reaches the skill without explicit approval.**

Locations:
- lessons log  - the project's `lessons-log.md`
- change-sets  - the project's `changesets/` folder
- change log   - the project's `CHANGELOG.md`
- the skill    - `${CLAUDE_PLUGIN_ROOT}/skills/data-center-schedule/`
                 (`references/06-lessons-learned.md`, `references/02-schedule-patterns.md`,
                 `MAINTENANCE.md`)

> **Phase numbering.** The phases below are scoped to the **harvest workflow** only -
> not the same phases as `/build-schedule`, `/update-schedule`, or the skill's build
> method. Each section leads with its name; the `harvest phase N` tag is just ordering.

## Gather · harvest phase 1
Read `lessons-log.md`. Then scan `changesets/` and `CHANGELOG.md` for signals that
were never logged - a change-set that corrected an earlier one, a flag that recurs
across versions - and treat those as additional candidates. Note any closed-out item
in the project's assumptions register: a resolved assumption is often a lesson.

## Harvest · harvest phase 2
Invoke the `lessons-harvester` subagent. It independently:
- deduplicates and clusters related entries, carrying every source citation
- cross-checks each candidate against the lessons ALREADY in the bundled skill, so
  nothing already covered is re-proposed - it may instead recommend merging into an
  existing numbered lesson
- categorizes each by home: `skill-lessons`, `skill-patterns`, `plugin`, or
  `project-only`
- recommends an action for each, and flags any candidate with weak or missing evidence

## Proposal preview · harvest phase 3
Present the harvest proposal as a table: candidate, home, recommended action
(promote new / merge into lesson #N / keep project-local / discard), and the source
citation. Call out separately any candidate with weak evidence and any existing skill
lesson a candidate would merge into.

## Approval gate · harvest phase 4  --  STOP
Do not proceed. The user decides each item.
- Approved items -> Promote.
- "keep project-local" / "discard" -> record the disposition in `lessons-log.md`, no
  skill change.
- Project-specific facts - real client decisions, real contractual dates, named
  people - are NEVER promoted. See the skill's `MAINTENANCE.md`, "What NOT to
  contribute".

## Promote · harvest phase 5
The skill is bundled inside this plugin, so promotion edits the plugin's own files -
there is no separate `.skill` to repackage. For each approved item, by home:
- **skill-lessons** -> append to
  `skills/data-center-schedule/references/06-lessons-learned.md` (numbered,
  accumulating - never reset the numbers), keeping the source citation on the entry.
- **skill-patterns** -> add to
  `skills/data-center-schedule/references/02-schedule-patterns.md`.
- **plugin** -> edit the relevant file in this plugin (a `docs/` page, a script, the
  change-set schema).

Then:
- bump the skill changelog at the top of `skills/data-center-schedule/SKILL.md`
- bump `plugin.json` - a lessons promotion is a material change
- update each promoted entry in `lessons-log.md`: status `promoted` (or `merged`),
  with a disposition naming the destination and the date
- apply any sanitization rules in the skill's `MAINTENANCE.md` ("What NOT to contribute")

## Hand off · harvest phase 6
- Summarize: lessons promoted, lessons merged, items kept project-local, discarded.
- Remind the user to commit and push the plugin repo so every device gets the
  update - the plugin carries the skill (see `docs/multi-device-setup.md`).
- Never overwrite a delivered artifact; the version bumps keep the history.

## Rules
- Never promote without the approval gate.
- Never promote project-specific facts into the skill.
- Every promoted lesson keeps its source citation.
- Deduplicate against the skill's existing lessons - the list grows with signal, not
  bloat.
- Bump the skill changelog and the plugin version on every promotion.
- The harvester proposes; it never edits the skill. Promotion happens here, after
  approval.
