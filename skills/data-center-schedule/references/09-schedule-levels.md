# Schedule Levels -- Density Classification (Level 1 to Level 5)

## Naming -- three different things are called "level"

Keep these separate; they collide constantly:

- **Schedule Level (Level 1-5)** -- THIS file. How dense the schedule is, from a
  milestone-only summary to a daily task list. The AACE schedule-classification
  scale, adapted to data centers.
- **Commissioning Level (L1-L5)** -- FAT / PFC / Functional / IST / Load Bank.
  A property of commissioning activities. See `02-schedule-patterns.md` section 3.
- **WBS Level** -- depth in the WBS tree (WBS level 1 = top branches). A
  structural property of the WBS.

When in doubt, write it out: "schedule Level 3", "commissioning L3", "WBS level 3".

## The five schedule levels

### Level 1 -- Milestone Schedule
- **Purpose:** executive and contractual tracking.
- **Audience:** owner executives, board, lenders.
- **Granularity:** contract milestones plus a handful of key gates only.
- **Size (4-DH project):** ~20-40 activities.
- **Includes:** EFA / FA / FR / RFS per DH, project start/finish, major utility
  energization (A-feed / B-feed), top-level area-complete gates.
- **Excludes:** all construction, procurement and commissioning detail.
- **Inputs needed:** milestone definitions + contractual dates.
- **Builder:** generated directly from the milestone set, or rolled up from L3.

### Level 2 -- Summary Schedule
- **Purpose:** management coordination at phase level.
- **Audience:** owner PM, GC PM.
- **Granularity:** one summary bar per area per discipline phase -- Procurement,
  Construction, Commissioning rolled up.
- **Size:** ~80-150 activities.
- **Includes:** per-DH per-discipline summary bars + all milestones.
- **Excludes:** activity-level detail and logic between summary bars.
- **Inputs needed:** area list, milestone dates, rough phase durations.
- **Builder:** generated directly, or rolled up from L3.

### Level 3 -- Control / CPM Schedule  (the canonical layer)
- **Purpose:** the working schedule -- sequences work across all subs and drives
  the contractual milestones. This is what "the reference project schedule" is.
- **Audience:** scheduler, GC, subcontractors.
- **Granularity:** activity-level, full predecessor logic, procurement-to-install
  ties, L2-L5 commissioning activities, per-DH catalog.
- **Size:** ~800-1500 activities for a 4-DH build (the reference project = ~1,130).
- **Includes:** the full per-DH activity catalog (`02-schedule-patterns.md`
  section 2) for every area, replicated with stagger.
- **Inputs needed:** trade detailed schedules, MEL, P6 templates, milestone defs.
- **Builder:** the full Phase 2-6 workflow.

### Level 4 -- Execution Schedule
- **Purpose:** crew-level execution planning.
- **Audience:** sub foremen, field leads.
- **Granularity:** each L3 activity decomposed into work packages -- e.g.
  "DH4 Branch Power" -> rough-in by zone, terminations by zone, testing by zone.
- **Size:** ~3,000-8,000 activities.
- **Inputs needed:** crew-level trade detail (work plans, look-aheads).
- **Builder:** explodes each L3 activity. **Where trade detail is absent it
  emits a structured shell** -- placeholder work packages under each L3 parent,
  every one flagged in the assumptions register for the trade to fill in.

### Level 5 -- Detailed Look-Ahead
- **Purpose:** short-interval (3-6 week) daily execution control.
- **Audience:** field crews.
- **Granularity:** daily tasks.
- **Size:** a rolling window only -- never the whole project at once.
- **Inputs needed:** trade 3-week look-aheads.
- **Builder:** scaffolds the window; populated from trade look-aheads each cycle.

## How the levels relate

Level 3 is the **canonical spine** -- one shared WBS and milestone set.

- **Level 1 and 2 are roll-ups of Level 3** -- summary views, no new information.
- **Level 4 and 5 are drill-downs of Level 3** -- each L3 activity decomposes
  into L4 packages and L5 daily tasks.

So a project can hold one schedule at multiple levels: build L3 once, generate
L1/L2 as summary exports, expand L4/L5 where trade data supports it. If the
target is L1 or L2 only, the builder can produce it directly without the full L3.

**Honest constraint:** L4 and L5 cannot be fully auto-generated -- they need
crew-level trade data a template cannot invent. Absent that data the builder
produces a decomposition *shell* and flags every placeholder. Do not present a
shell as a real L4/L5 schedule.

## Picking a level

| You need... | Build at |
|---|---|
| A board / lender view, or a contract-date tracker | Level 1 |
| A management coordination view across areas | Level 2 |
| A schedule that sequences subs and drives milestones | Level 3 |
| Crew-level execution planning | Level 4 |
| A short-interval daily look-ahead | Level 5 |

Most owner-side hyperscale schedules live at **Level 3**. Build L3 first; derive
the others from it.
