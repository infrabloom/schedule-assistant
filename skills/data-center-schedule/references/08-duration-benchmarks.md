# Duration Benchmarks -- Reusable Starting Durations for DC Schedules

Benchmark ranges for a high-level (schedule Level 3) hyperscale data center
schedule, in **8h-day working days** unless noted. Two uses:

1. **Sanity-check trade-reported durations.** If a trade quotes a number far
   outside these ranges, ask why before accepting it. Template defaults are
   often 3-10x low (lesson #6); trade numbers can also be padded.
2. **Seed a minimal-input build.** When a project starts with only a
   description, the `/build-schedule` from-description mode uses these to give
   every activity a duration -- each one then flagged in the assumptions
   register as benchmark-derived, to be replaced with trade-confirmed numbers.

**These are not gospel.** They are generalized from prior hyperscale builds.
Always confirm with the responsible trade and record the source in the
assumptions register. Durations scale with quantity -- multiply per-unit
figures by the area's unit count.

## Procurement lead time (PO -> delivery, in WEEKS)

| Equipment | Lead time (wk) |
|---|---|
| Power transformers | 30-60 |
| Generators | 40-60 |
| MV switchgear | 30-50 |
| Chillers | 25-40 |
| STS (static transfer switch) | 20-30 |
| UPS modules | 20-35 |
| CDU (coolant distribution unit) | 20-30 |
| Dry coolers | 16-24 |
| Fan Wall units | 12-20 |
| ATS / switchboards / panelboards | 12-20 |
| Commodity (cable, conduit, pipe, tray) | 4-10 |

## Facility staging long-leads (often "by others")

The front-end stages of a data center build usually sit outside an owner-side
construction schedule but are hard predecessors to energization. Track them as
long-lead constraints (see `references/11-infrastructure-primer.md`).

| Stage | Lead time |
|---|---|
| Entitled land (title + zoning) | months to years |
| Utility connections (power, water, sewer) | months to years |
| Site grading / pad | a few months |
| **Electrical substation** | **12-18 months -- commonly the schedule's long pole** |

The substation gates every A-feed / B-feed energization milestone. If it is on
an 18-month lead, that sets the earliest possible energization date -- surface
it in Phase 1.

## Construction -- Mech Room electrical (per DH, 8h-days)

| Activity family | Days |
|---|---|
| Set MV switchboard | 5-10 |
| Set transformers | 5-10 |
| LV switchgear install | 5-10 |
| Set UPS line-ups (HUPS / MUPS / CUPS) | 8-15 |
| Distribution switchboards install | 5-10 |
| MV / LV / UPS feeder pulls | 10-20 |
| Terminations | 10-20 |
| Cable testing | 5-10 |
| MV switchgear pre-Cx testing | 5-10 |

## Construction -- Mech Room mechanical (per DH, 8h-days)

| Activity family | Days |
|---|---|
| Supplemental steel + WBAs | 5-10 |
| CWS / CWR mains | 10-20 |
| CHWS / CHWR mains | 10-20 |
| Chiller rig & set (each) | 2-4 |
| Expansion / buffer tanks (each group) | 3-6 |
| Specialty piping | 10-20 |
| Supply / exhaust fans | 5-10 |
| Ductwork | 8-15 |

## Construction -- Data Hall (per DH, 8h-days)

| Activity family | Days |
|---|---|
| Floor flatness | 3-6 |
| HAC install (full bank) | 10-20 |
| MDB galleries (E + W) | 8-15 |
| HAC power pull + terminations | 8-15 |
| Cable tray | 5-12 |
| Networking racks | 5-12 |
| STS / ATS install | 3-8 |
| ISP/OSP fiber, IDF cabinets, production copper | 5-15 |
| Fire alarm wire pulls + device install | 8-15 |
| Fire suppression | 8-15 |
| Lighting | 5-10 |
| CDU piping | 8-15 |
| Security cabling + cameras | 5-12 |
| Deep clean | 3-6 |
| ISO-8 cleanliness test | 1-3 |

## Flush & Fill -- per loop (CHW / CW / PCW), 8h-days

Run in this order (lesson #37 -- flush first, fill second):

| Step | Days |
|---|---|
| Pneumatic test | 2-3 |
| Hydrostatic test | 4-6 |
| Flush / clean / passivate | 5-8 |
| Drain | 2-4 |
| First fill | 4-7 |
| Pump startup | 3-6 |
| Chiller vendor startup | 8-12 |
| Test & Cx | 8-12 |

## Commissioning (8h-days)

| Activity family | Days |
|---|---|
| L2 PFC, per discipline (MV/LV/UPS/XFMR/CHW/CW/PCW/FA/FS) | 3-8 |
| L3 functional / energization, per loop | 5-15 |
| L4 IST scenario, each (blackout, gen fail, chiller fail, ATS fail, EPO...) | 1-3 |
| L4 endurance run | 3-5 |
| L5 load bank step (25 / 50 / 75 / 100%) | 1-2 each |
| IT ramp-up | trade/owner-driven -- confirm |

## Yard (per DH or site-wide, 8h-days)

| Activity family | Days |
|---|---|
| Underground ductbanks | 10-25 |
| Generator pads | 5-10 |
| Generator set / anchor / connect | 8-15 |
| Yard MV switchgear | 8-15 |

## Calibration from completed reference projects

The bundled reference templates were checked against these benchmarks
(see `references/12-reference-template-library.md`). As-built schedules true up
planned dates to actuals at closeout, so their durations are realized durations
-- a trustworthy cross-check. A still-live reference schedule showed ~46% of
multi-day activities running longer than planned, the upper quartile at ~2x.
**Use these ranges, but carry duration contingency** -- the real-world overrun
tail is heavy and one-sided.

## How to use this file

- At Phase 3, compare every trade-reported duration to the matching range.
  Flag and question the outliers; never silently accept or silently override.
- For a minimal-input build, take the mid-point of the range, mark the activity
  `duration_source = benchmark` in the catalog, and list it in the assumptions
  register for trade confirmation.
- When a project closes, update these ranges with what the trades actually
  delivered (see `MAINTENANCE.md`).
