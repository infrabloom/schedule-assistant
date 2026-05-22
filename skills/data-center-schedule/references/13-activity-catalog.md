# Activity Catalog -- Distilled From the Reference Templates

A catalog of the activity TYPES that actually appear in real hyperscale data
center construction schedules, distilled from the three bundled reference
templates (see `references/12-reference-template-library.md`). It answers, for a
new build, "what activities should the schedule contain, and how long do they
typically run?" -- a granular companion to the duration RANGES in
`08-duration-benchmarks.md` and the WBS structure in `02-schedule-patterns.md`.

Durations are the **median planned duration** observed across the templates, in
8h-day working days -- realistic starting points, confirm with the trade
(lesson #6). Names are generic activity TYPES; a real schedule carries many
per-unit instances of each (e.g. one "QC" activity per switchboard).

## Equipment delivery (owner/contractor-furnished -- OFCI / CFCI)

| Activity type | Typical |
|---|---|
| Packaged power module / PDU set on site | ~25 d |
| MV transformer set | ~10 d |
| Generator set | ~10 d |
| UPS line-up set | ~10 d |
| Air handler (DAHU) set | ~10 d |
| Exhaust fans set | ~10 d |
| ATS set | ~10 d |
| Cable bus set | ~10 d |

OFCI = Owner-Furnished, Contractor-Installed; CFCI = Contractor-Furnished,
Contractor-Installed. These are long-lead items -- tie them to procurement
(`08-duration-benchmarks.md`).

## Electrical construction

| Activity type | Typical |
|---|---|
| Cable bus install | ~10 d |
| Pull equipment / air-handler feeders | ~5 d |
| Branch conduit / branch wiring | ~5 d |
| Exhaust-unit electrical | ~5 d |
| Equipment panel -- setting | ~1 d |
| Equipment panel -- wiring | ~3 d |
| Panel-to-controls wiring | ~5 d |

## Mechanical / cooling

| Activity type | Typical |
|---|---|
| Branch piping (mechanical) | ~5 d |
| Piping to generator | ~3 d |
| Domestic water line -- install / test / insulate | ~4 d |
| Industrial-water overhead lines | ~2 d |
| Pull air-handler (DAHU) feeders | ~5 d |

## Fire & life safety

| Activity type | Typical |
|---|---|
| Sprinkler install | ~3 d |
| Data-hall fire protection install | ~5 d |
| VESDA (very-early smoke detection) install | ~3 d |

## Fuel & generator system

| Activity type | Typical |
|---|---|
| Fuel train installation | ~1 d |
| Fuel skid / pipe connections | ~1 d |
| Generator fuel panel -- setting | ~1 d |
| Generator fuel panel -- wiring | ~3 d |
| Generator fuel panel -- accessories | ~1 d |
| Fuel-panel-to-controls wiring | ~5 d |
| Generator fuel-system startup | ~1 d |

## Commissioning -- the per-equipment start-up micro-chain

The templates' single most repeated logic pattern: **every major equipment
assembly** (switchgear, transformer, UPS, ATS, PDU, generator, air handler)
runs the same short start-up chain. Replicate it per equipment item:

```
Construction Complete -> QC (1-3 d) -> IEM (1-2 d)
   -> FOD & Equipment Energization (~2 d)
   -> Start-up Complete (1-3 d) -> Start-up Report Received (~1 d)
```

Total ~6-12 working days per equipment assembly. QC = quality check;
IEM = initial equipment-maintenance check; FOD = foreign-object-debris
clearance before energization. This micro-chain is a clean reusable fragnet --
the L2 -> L3 commissioning detail that sits under each equipment item.

## How to use this catalog

- In Phase 3, use it as a checklist -- does the new schedule have an activity
  for each type relevant to its scope?
- Use the typical durations as first-pass numbers, flagged in the assumptions
  register for trade confirmation.
- For per-equipment commissioning detail, stamp the start-up micro-chain onto
  every major equipment assembly.
- This catalog lists observed activity TYPES; the full per-project activity
  list and its logic are best read directly from the closest template in Phase 1.
