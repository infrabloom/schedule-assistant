# Maintaining and Improving This Skill

This file is for any future Claude session asked to update the `data-center-schedule` skill with lessons from a wrapped project. Read this **before** making changes.

## The contribution model

The skill compounds in value when every completed DC project contributes back **at least one** of these four things:

1. **A sanitized reference XER** — added to `assets/p6-templates/`
2. **New lessons learned** — appended to `references/06-lessons-learned.md`
3. **New patterns** — added to `references/02-schedule-patterns.md`
4. **Exemplar deliverables** — added to `assets/exemplars/`

The XER is the highest-value contribution because Phase 1 of every future project starts by reading these templates.

## How lessons reach this file (the capture-review-promote pipeline)

Lesson candidates are captured continuously while a project runs. The 7-phase
workflow has **[CAPTURE]** steps at Phases 3/4/6 and a **Phase 7 build retrospective**
(see `references/01-phased-workflow.md`), and the schedule-assistant plugin's
`/update-schedule` captures from every update run. All of them append to the
project's `lessons-log.md`.

That log is the structured input to this maintenance flow. The plugin's
`/harvest-lessons` command reviews the log, deduplicates against the lessons already
here, and proposes promotions for the user to approve. "Update the skill with what we
learned" is the same sequence described below — just fed by the log instead of memory.
Capture is automatic; promotion (the steps below) still needs explicit user approval.

## When the user says "update the skill with what we learned on [project]"

Follow this sequence:

### Step 1 — Discovery pass

Read the project's `lessons-log.md` first — it is the structured capture log and your
primary source. Then read the project's outputs folder for anything the log missed.
You're looking for:
- The final approved XER (e.g., `[Project]-Schedule-v4.X.xer`)
- The final narrative document (`[Project]-Schedule-Narrative-v4.X.md`)
- The PM briefing, open-items list, assumptions register
- Any "lessons learned" or "post-mortem" notes the user wrote during the project
- The assumptions register — every closed-out assumption is a candidate lesson

Summarize what you found. **Stop and ask the user** to confirm which items to add to the skill. Don't decide unilaterally.

### Step 2 — Sanitize the XER

Use `scripts/sanitize_xer.py` to strip the real project XER down to a reusable template.

```bash
# First, generate a config template
python scripts/sanitize_xer.py [Project]-Schedule-v4.X.xer /tmp/out.xer \
    --print-default-config > /tmp/scrub-config.json

# Edit /tmp/scrub-config.json — fill in real names to scrub
# (e.g., for CB4: replace "CB4" → "DC-TMPL", "Terawulf" → "OWNER",
#  "FluidStack" → "CLIENT", "MLP" → "MECH-INSTALL",
#  "DAF" → "MECH-CX", "OCE" → "ELEC-CONTRACTOR",
#  "Lake Mariner" → "SITE-LOC", etc.)

# Then run the sanitizer
python scripts/sanitize_xer.py [Project]-Schedule-v4.X.xer \
    assets/p6-templates/[Project-Sanitized]-Template.xer \
    --config /tmp/scrub-config.json
```

The sanitizer:
- Renames PROJECT to a generic template label
- Resets all actuals (TK_Active/TK_Complete → TK_NotStart, clears act_start/act_end, resets pct/remain)
- Replaces project-specific strings across activity names and WBS names
- Regenerates GUIDs (so the template can coexist with the original in OPC)
- Strips cost data
- Optionally re-baselines target dates by a day offset

After sanitization, **always**:
1. Validate the output: `python scripts/validate_xer.py assets/p6-templates/[New-Template].xer`
2. Spot-check 5-10 activity names and the PROJECT row for any leftover client-specific strings
3. Show the user the sanitization diff (a few sample before/after rows) before adding to the skill

### Naming convention for reference XERs

Use `[Project]-[Region]-[Year]-Template.xer`. Examples:
- `CB4-NY-2026-Template.xer`
- `CB5-TX-2027-Template.xer`
- `DC8-VA-2027-Template.xer`

This makes it easy at Phase 1 to pick the closest reference for a new project (geography + scale + year).

### Step 3 — Append lessons learned

For each new pitfall the project surfaced, append to `references/06-lessons-learned.md` under a new section:

```markdown
## [Project] Lessons (added YYYY-MM-DD)

### N. [Short title of the pitfall]

**What happened on [Project]:** [Concrete description — what we did, what broke]

**Fix:** [What to do instead next time]

**Validation:** [How to detect this proactively — script check, manual spot-check, etc.]
```

Keep the numbered list growing. Don't reset numbers per project — they accumulate.

### Step 4 — Add patterns if applicable

If the project revealed a structural pattern not already in the patterns reference, edit `references/02-schedule-patterns.md`. Examples of things that would warrant a pattern addition:

- New cooling architecture (direct-liquid, hybrid, air-cooled)
- Different DH count (8 DHs instead of 4)
- New commissioning level (e.g., L6 if owner adds one)
- New procurement-to-install convention
- Different stagger pattern (parallel vs sequential crews)

### Step 5 — Optional: add an exemplar deliverable

If the project produced an unusually clean deliverable (PM briefing, critical path analysis, fragnet), copy a sanitized version to `assets/exemplars/[Project]-PM-Briefing.md`. Sanitize the same way as the XER — strip names, dates, dollar amounts.

### Step 6 — Bump the version

Add a changelog entry at the top of `SKILL.md` (right after the frontmatter):

```markdown
<!-- Changelog
v1.0 (2026-05): Initial release from CB4 build
v1.1 (2026-XX): Added CB4-NY-2026 template; lessons 19-23 from CB4 wrap-up
v1.2 (2026-XX): ...
-->
```

### Step 7 — Validate and commit

This skill is **bundled inside the schedule-assistant plugin** — it lives at
`skills/data-center-schedule/` in the plugin tree. There is no separate `.skill`
file to repackage; "handing it back" means committing the plugin so every device
picks the change up.

```bash
# From the plugin root
python -m unittest discover -s tests          # the pipeline suite still passes

# Validate any new bundled template
python skills/data-center-schedule/scripts/validate_xer.py \
    skills/data-center-schedule/assets/p6-templates/[New-Template].xer
```

Then commit and push the plugin repository (or let it sync — see
`docs/multi-device-setup.md`). A skill change is a plugin change, so bump
`plugin.json` as well as the SKILL.md changelog.

Summarize for the user what changed: new template name, lessons added, the
SKILL.md version bump, and the plugin version bump.

## Adding a new reference file

The `references/` directory uses a fixed two-digit prefix (`01`–`13`). Those
numbers are **append-only and stable**:

- A new reference takes the **next free number** — `14`, then `15`, and so on.
- **Never renumber or reorder** existing references. `SKILL.md`, the agents, the
  commands, and project configs all cross-reference them by number; renumbering
  silently breaks every one of those references.
- The number is an identifier, not a reading order. A new reference that belongs
  logically "early" still gets the next free number — that is fine.

To add one:
1. Create `references/NN-short-name.md` with the next free `NN`.
2. Register it in the reference table in `SKILL.md` (the "open the reference
   file that matches your task" table) so the skill knows it exists.
3. Bump the SKILL.md changelog and `plugin.json`.

## Sanitization quick checklist

Before declaring a sanitized XER safe to bundle, manually verify:

- [ ] No client name in PROJECT row
- [ ] No contractor names (MLP / DAF / OCE / etc.) in activity descriptions
- [ ] No site / geographic names (Lake Mariner / VA / IN / etc.)
- [ ] No actuals (every status_code = TK_NotStart)
- [ ] No dates within 30 days of the original data date (if dates left in, makes the project identifiable)
- [ ] No costs / dollar amounts
- [ ] No vendor PO numbers
- [ ] No personal names in notes or comments
- [ ] GUIDs regenerated (so it doesn't collide with the original in OPC)
- [ ] WBS names scrubbed (Admin Building OK, "Admin Building - Client XYZ" not OK)
- [ ] `validate_xer.py` passes

If any item fails, fix in the sanitizer config or by post-editing the XER.

## What NOT to contribute

These are project-specific and should never enter the skill:

- Real contractual dates
- Real client decisions / interpretations (e.g., "Client X said EFA means racks-energized")
- Real assumptions register entries that name people
- Real critical-path activity codes (the *pattern* is fine, the specific paths are project)
- Trade-specific quirks (e.g., "MLP always uses 480V instead of 277V") unless generalized

When in doubt: would this be embarrassing or contractually problematic if a competitor saw the bundled skill? If yes, don't include it.

## Frequency of updates

After each project that produces a real schedule, plan 2-3 hours to do this. Once the work is fresh in the user's head, the lessons-learned step takes 30 min and the sanitize+package takes another 30 min. Doing it months later is much harder.

## A note on description tuning

After 3-4 projects worth of contributions, consider running the skill-creator's description optimizer to fine-tune triggering. By then you'll have a better sense of which queries the skill should grab (and which it should pass on to other skills). The description tuning step is in skill-creator's main SKILL.md under "Description Optimization."
