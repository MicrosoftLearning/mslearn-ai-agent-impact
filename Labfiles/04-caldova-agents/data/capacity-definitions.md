# Caldova capacity definitions

All records are synthetic. Use the frozen decision date of October 1, 2026, and a launch date of November 30, 2026. Do not substitute today's date.

| Concept | Definition | Evidence |
|---|---|---|
| Plant | A UK manufacturing site with one listed sterile fill-finish line | CAP-01 through CAP-03 |
| Batch | A released production lot. Held or unreleased batches contribute zero available units | POL-01 |
| Baseline | 100,000 units of approved production across all three plants for the launch window | BASE-01 |
| Capacity gap | An additional 7% of the fixed baseline, or 7,000 units | BASE-01 |
| Available capacity | Additional released, usable units during the launch window, after existing commitments and downtime. Do not subtract commitments again | CAP-01 through CAP-03 |
| Remaining gap | max(0, 7,000 minus usable internal additional units) | BASE-01 and CAP records |
| Qualified CMO | Approved status and a valid ISO date for qualification expiry on or after the launch date | POL-01 |
| Compliance status | Lab policy checks for qualification, UK location, released batches, audit references, and readiness by launch. This is not regulatory certification | POL-01 |

The legacy planning export calls plant N-SF1 `UK-NORTH-01` and reports 12,000 *gross* units. Record LEG-01 is a conflicting definition, not another 12,000 available units. The authoritative binding maps both identifiers to Caldova North and uses CAP-01's 2,000 net additional units. Do not add the legacy figure to the capacity calculation.

Required recommendation evidence: frozen dates, baseline, gap, units and scope, each plant's net additional capacity, batch status, supplier qualification dates, supplier readiness, cost, region, and audit IDs. Unit costs exclude transfer and validation costs. A cheaper unit price alone is not an approved commercial decision.
