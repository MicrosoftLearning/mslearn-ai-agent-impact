# Caldova L400 BYOS readiness and delivery contract

This supplement supports the [six-hour workshop](../../index.md). It extends, rather than replaces, the [original integration-pack requirements](README.md). The runtime source, deployment definitions and supporting material are included; configure the actual connections and tenant resources before exercising the hosted paths.

> **Setup:** Use [tenant and workstation setup](../../Instructions/Setup.md). The assigned administrator supplies tenant settings, identities and connections; the engineer implements and verifies the runtime during the hands-on exercises.

## Scope and source authority

Use the supplied case study for Caldova's customer context and the design document for the implementation/deployment and troubleshooting/optimization outcomes. The design describes an 11-hour course with additional instruction and discussion. This workshop allocates exactly 360 working minutes to hands-on exercises only. Do not use the case study's material after its explicit reference cutoff as a binding implementation specification.

The six core CSVs are the primary operational dataset. The original JSON fixture is an intentionally separate fault harness. Do not edit core country values to make them UK values, replace its 18,900-unit gap with 2,500, or fabricate expiry dates. Core supplier selection is provisional decision support, not proof of qualification through launch. The customer's UK processing requirement requires actual service-region and data-flow evidence, not a manufacturing-country filter.

## Required local environment record

Record actual values in the local BYOS environment record; never commit it:

| Area | Required values and tested artifacts |
| --- | --- |
| Workspace | Assigned identity, subscription, approved regions, Fabric capacity/workspace, isolation boundary, quotas, and cleanup owner |
| Runtime package | Source repository/ref and working directory; pinned Python/SDK versions; dependency manifest; build, unit-test, start, deploy, smoke-test, and rollback commands |
| Deployment identity | Foundry endpoint, model deployment, managed identities, authorization scopes, container image digest, configuration file path, health/log URLs, and secret-injection mechanism |
| Data adapters | Read-only core source, event query connection, ontology ID, policy knowledge-base ID, source snapshot/version, and stable record-reference scheme |
| Procurement | SharePoint site/list URLs, approved directory and RFP seed, `RecordFollowUp` flow, lab group, and in-group/out-of-group accounts |
| Evidence | Approved evidence store, trace exporter, identity crosswalk, registry exporter, retention period, and source-access audit view |
| Fault and recovery | Isolated qualification-fixture endpoint, deployment source path, seeded integration incident, test scraper, denial test, reset commands, and checkpoints |

Never include credentials, connection strings, or bearer tokens in Git or the handout. Inject credentials using approved runtime/environment mechanisms. The supplied simulator uses an Event Hubs-compatible connection string, unlike the managed-identity hosted agents; scope and rotate that simulation-only credential.

## Runtime implementation contract

The repository implementation must deliver editable, tested source code, not a prompt-only agent or a prerecorded deployment. Learners complete and deploy changes to that code.

| Component | Required behavior and preflight evidence |
| --- | --- |
| `AssessCoreCapacity` | Read the six curated tables, use `launch_program` as gap authority, and filter/rank suppliers exactly as the supplied notebook. Return raw evidence references and a source version, not invented expiry or UK-manufacturing status. |
| `ValidateCoreDecision` | Independently recompute LP001 gap and core eligibility from the trusted snapshot; validate proposed IDs/order, required evidence, profile, and incomplete-readiness disclosure. Reject changed gap/unknown IDs, missing evidence, failed tools, or mismatched versions. Use policy ID `CORE-LP001-v1`, not POL-01. |
| Core policy knowledge | Publish the supplied [core profile instructions](l400-core-agent-instructions.md) as the approved lab policy with an explicit provisional-approval rule. This is a training policy, not a customer-validated GxP procedure. |
| Orchestrator | Explicit server-side profile selection; authenticated typed tool calls; conditional sourcing; a draft state; guardrail invocation before every final result; fail-closed exception/error handling with logged reasons; real trace correlation. User text cannot select arbitrary files, versions, identities, or tool endpoints. |
| Hosted guardrail | Actual GitHub Copilot SDK session and registered deterministic tools. Use `ValidateCoreDecision` only for core and `gxp_checks.check` only for the fixture. A verdict from one profile cannot release the other. |
| Fixture adapter | `AssessCandidates` packages the learner's `capacity_tool.py`, `qualification.py`, and `policy.py`; executes only allowlisted scenario IDs; exposes the three frozen cases and the original structured export contract. |
| Operational events | Read-only Eventhouse access and a query/export path that returns EventID, SourceSystem, timestamps, and source version. Restrict to one replay cohort, deduplicate by EventID, and never alter the authoritative launch gap. |
| Error injection | Test-only mode for tool timeout, missing verdict, and wrong source version with bounded durations. No production permissions, live crawler, or real data exfiltration. |
| Tracing and evaluation | Trace/tool order, profile, source version, deployed revision, tool identities, durations, token counts when available, and source references. Export actual runs and a normalized six-agent registry. Enable built-in evaluators on supported targets. |

Provide repository-standard tests covering the above contracts. In particular, a repaired fixture must not switch the production/core decision path to the fixture dataset. Keep regression fixtures out of production-facing prompt context and don't disclose evaluation answer keys to the agents.

## Preflight and checkpoint gates

Use a learner-equivalent identity and retain real results. Complete and validate the BYOS setup before the timed workshop, but leave the assigned implementation/configuration work for learners.

| Checkpoint | Required recovery state (not an existing checkpoint) | Smoke test |
| --- | --- | --- |
| D0 | Source assets, approved workspace/capacity, editable notebook; empty learner runtime configuration | Core CSV access and local baseline tests work |
| D1 | D0 plus curated tables, event pipeline, ontology, and scoped runtime data connection | 318 rows, LP001 18,900 gap, 10 events and four breaches for one replay |
| D2 | D1 plus procurement agent, append-only flow, scoped Teams publication | Citation, actual receipt, idempotent retry, and denied manufacturing read |
| D3 | D2 plus connected core runtime, SDK guardrail, isolated faulty fixture endpoint, test scraper | Core result gated before release; fixture shortlist rejected by POL-01 |
| D4 | Reviewed repair and remote deployment, evaluation/export environment | Three fixture cases export exactly once; core still uses core rules |

Restoration is recovery, not evidence the learner implemented that task. A prerecorded walkthrough doesn't satisfy either learning outcome. If a required integration is unavailable, mark its tasks **Blocked** and reschedule or provide the tested environment.

## Pilot acceptance

Before delivery, verify the notebook imports and dates parse, Eventhouse receives only the intended replay cohort, and nested solution instructions can be followed without undocumented tool choices. Record regional preview availability and applicable data-processing terms. Do not enable cross-geo processing merely to make the demo pass a UI check.

Confirm a real core call produces 270,000 target units, 251,100 qualified units, an 18,900-unit gap, PL003 binding plant, eight delayed batches, and the provisional order CMO001, CMO002, CMO006. Confirm that CMO006's simulated nine-week signal is reported separately from its eight-week core lead-time field. The signal is a freshness conflict requiring investigation, not automatic qualification revocation or an approved new capacity plan.

Seed the qualification defect only in the isolated fixture adapter. Verify nine baseline and eight evaluator tests pass while two regression tests fail. After the instructor repair, verify all 19 existing tests pass and the three fixture outcomes match the original pack. Verify empty/missing/error guardrail results withhold a positive answer for both profiles.

Pilot all four exercise time boxes, including deployment wait time, evidence collection, and cleanup. Adjust scope or provision warm resources if the pilot exceeds six hours. Report tested Python/SDK versions, test command results, UTC preflight time, and remaining blockers. This document is a contract, not a record that these checks have passed.
