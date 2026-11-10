---
lab:
    title: 'Establish trusted Caldova operational context'
    description: 'Curate source data, replay operational signals, and establish authoritative agent context.'
    level: 400
    duration: 75
    islab: true
---

# Exercise 01: Establish trusted operational context

> **Repository:** Start with [setup](../Setup.md) and the [runtime guide](../Runtime.md). Use your assigned tenant and check the actual results of each hands-on task.

## Scenario

Caldova's earlier agents used conflicting definitions of available capacity. You establish a reproducible operational baseline before connecting any agent to the data. You use the supplied core data as the main decision source and retain the smaller qualification fixture only for later fault isolation.

## Objectives

After you complete this exercise, you'll be able to:

- Curate six source tables and verify their typed keys and LP001 decision evidence.
- Replay and diagnose synthetic operational events without changing the authoritative gap.
- Bind a governed business vocabulary and verify the runtime's permitted source access.

## Duration

**Estimated time:** 75 minutes

## Task 01: Curate and verify the core data

### Introduction

Peter's decision depends on the launch plan, not on whichever capacity field an agent happens to retrieve first. The core files describe a multinational operational estate, while Caldova's UK policy concerns approved processing and regulated-data handling.

### Description

In this task, you'll establish the source manifest, load six core CSVs into a Lakehouse, and validate the LP001 baseline. **Estimated time:** 25 minutes.

### Success criteria

- Six typed Delta tables contain 318 rows and pass the supplied relationship checks.
- LP001 reports 270,000 target units, 251,100 qualified units, an 18,900-unit gap, and PL003 as its binding plant.
- The evidence manifest distinguishes core data from the isolated qualification fixture.

### Learning resource

- [Core curation notebook](../../Allfiles/L300-TW-Data/notebooks/curate_caldova_tables.ipynb)
- [Core business definitions](../../Allfiles/L300-TW-Data/agent/business-context-instructions.txt)

### Key tasks

#### Key task 01: Establish your working copy and source manifest

Identify exactly which assets you use before creating cloud resources.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. In VS Code use **Git: Clone** (**Ctrl+Shift+P**) to clone the assigned Caldova lab repository and tested revision. After the approved changes are merged, use `https://github.com/MicrosoftLearning/mslearn-ai-agent-impact.git`. Before then, use the instructor-supplied fork, branch and commit. Keep learner edits in a local working branch.
1. Open the [workshop introduction](../../index.md) and the [BYOS setup and local environment record](../Setup.md). Verify the assigned workspace, identities, approved regions, and evidence store. Record the repository commit and the start time in UTC.
1. Inspect `Allfiles\L300-TW-Data\data\core`. Record the six filenames, their primary keys, and the expected table mapping: launch program to `launch_program`, products to `product`, plants to `plant`, manufacturing capacity plan to `capacity_plan`, manufacturing batch schedule to `batch`, and procurement CMO evaluation to `supplier`.
1. Record `core` as the main profile. Record the JSON fixture under `Labfiles\04-caldova-agents\data` as a separate repair harness. Compare the dates, IDs, and quantities in the workshop's profile table.
1. Verify that your source manifest doesn't claim the core plants are all in the UK. Keep actual processing-location approval as a separate requirement.

    **Expected result:** The manifest identifies the correct source version and preserves the distinction between country fields, processing residency, and fixture data.

</details>

#### Key task 02: Curate the source tables

Use the supplied notebook rather than manually inferring CSV types.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Complete the [capacity and workspace setup](../Fabric-Foundation.md) if this environment has no assigned capacity/workspace. Reuse recorded resources when resuming.
1. Open the assigned workspace in [Microsoft Fabric](https://app.fabric.microsoft.com). Create a learner-owned Lakehouse named `caldova_l400` in the approved capacity. Record its actual item ID. Don't reuse a production Lakehouse.
1. Create a `caldova-data` folder under the Lakehouse's **Files** area and upload all six files from `Allfiles\L300-TW-Data\data\core`. Keep their names unchanged.
1. Import `Allfiles\L300-TW-Data\notebooks\curate_caldova_tables.ipynb` into the workspace and attach `caldova_l400` as its default Lakehouse.
1. Inspect the notebook's `DATA_ROOT` and explicit schemas. Confirm the path is `Files/caldova-data`. Review the date conversion for ordinal supplier audit dates and the table-overwrite behavior before you run it.

    > **Warning:** The notebook overwrites its six named tables. Run it only against your isolated Lakehouse.

1. Run the notebook cells in order and inspect the row-count and relationship-validation output. Expect 10 launch programs, 25 products, five plants, 60 capacity plans, 212 batches, and six suppliers.
1. Inspect date columns for failed conversions. The supplied supplier cell uses doubled backslashes in raw regular expressions, which can prevent removal of ordinal suffixes and normalization of `Sept`. Capture the failure or null result, then remove the original `LastAuditDate` `.withColumn` transformation from the supplier CSV-read chain so `supplier` retains the source strings. Add this standalone transformation immediately after that read and before its `write_table` call. It normalizes source text without changing the business date. Rerun the cell and verify all six audit dates are non-null, including September 22, 2025 for CMO002.

    ```python
    supplier = supplier.withColumn(
        "LastAuditDate",
        F.to_date(
            F.regexp_replace(
                F.regexp_replace("LastAuditDate", r"(?i)(?<=\d)(st|nd|rd|th)", ""),
                r"(?i)\bSept\b", "Sep",
            ),
            "d MMM yyyy",
        ),
    )
    ```

    Replace the original transformation in the CSV-read chain rather than applying this code after the date has already become null. Preserve the source CSVs and retain the before/after evidence. If your prepared notebook already contains the reviewed correction, verify it instead of applying it twice.

    1. Rerun the notebook's **Final date checkpoint** after the repair. It must reject null required dates and verify CMO002 is September 22, 2025. A row-count/relationship pass alone is not final curation success. Retain the before/after outputs.

    **Expected result:** All six tables are present, their counts sum to 318, relationships have no orphans, and the final date checkpoint passes.

</details>

#### Key task 03: Verify the decision baseline

The notebook's final queries are the reference for operational quantities and provisional supplier selection.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Run the notebook's final decision-query cell. Verify LP001, P101, the November 26, 2026 launch date in `launch_program`, the 18,900-unit gap, PL003, and eight delayed batches.
1. Compare the three LP001 capacity-plan rows with the launch plan. Note the negative availability and the separate utilization observations. Don't sum all 60 rows or treat utilization percentage as units.
1. Review the supplier query. Confirm that eligible rows satisfy sufficient capacity, `Currently valid`, zero critical findings, and `FastTrackEligible = Yes`, in order CMO001, CMO002, CMO006.
1. Record that the dataset lacks qualification-expiry dates and complete transfer approvals. Mark final approval through launch **Blocked pending quality evidence**, not passed because the supplier is currently valid.
1. Save the notebook outputs, source manifest, and item IDs in your approved evidence store. Compare them with the success criteria before proceeding.

    **Expected result:** Your baseline is reproducible from the core files and doesn't contain the repair fixture's 4,500 or 2,500-unit quantities.

</details>

Congratulations! You've established Caldova's authoritative operational baseline and a reproducible source manifest for the decision team.

## Task 02: Replay and investigate operational signals

### Introduction

A launch plan is a snapshot. Operational signals can reveal that the snapshot needs investigation, but they don't silently become a revised capacity plan. You retain both source meaning and event provenance.

### Description

In this task, you'll configure an Eventhouse destination, replay the supplied events, and verify a bounded set of simulated exceptions. **Estimated time:** 25 minutes.

### Success criteria

- The typed `operational_events` table receives one complete 10-event replay.
- A replay-scoped, deduplicated query returns four strict threshold breaches.
- The agent evidence distinguishes simulation, current replay time, and the frozen business plan.

### Learning resource

- [Eventstream custom endpoints](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/add-source-custom-app)
- [Publisher](../../Allfiles/L300-TW-Data/event-simulator/replay_events.py) and [table/mapping/query script](../../Allfiles/L300-TW-Data/event-simulator/detect_operational_exceptions.kql)

### Key tasks

#### Key task 01: Create the typed destination and source

Preserve the supplied event schema rather than relying on a partially inferred first event.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Create an Eventhouse in your assigned workspace and open its KQL database. Run the `.create table` statement from `detect_operational_exceptions.kql` to create `operational_events`.
1. Run the mapping statement from the same file. Confirm that `MetricValue` and `Threshold` are real numbers, `EventTime` is datetime, and the business IDs are strings.
1. Create an Eventstream with a **Custom endpoint** source. Configure the Event Hubs-compatible protocol supported by the supplied publisher.
1. Publish the **Custom endpoint** source first. Retrieve its Event Hubs-compatible connection string and entity name through the approved secret mechanism. Keep both out of Git, screenshots and agent chat. Publish a topology that has no finished destination if the wizard requires incoming data.
1. Continue to **Validate and replay the event cohort** below. Complete its dry run and dependency setup before opening a destination wizard. If the wizard needs schema data, send the single priming event there before completing the destination.

    **Expected result:** The typed table and mapping exist and the published source can receive simulation events. A published source alone does not prove a completed destination or ingestion.

</details>

#### Key task 02: Validate and replay the event cohort

Each publisher invocation generates new EventIDs. Select one replay cohort instead of counting everything ever received.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open a PowerShell terminal at the repository root. Create an isolated simulator environment and validate the event templates without sending anything. These commands use no cloud credential during dry run.

    ```powershell
    python -m venv .venv-caldova-stream
    .\.venv-caldova-stream\Scripts\python.exe .\Allfiles\L300-TW-Data\event-simulator\replay_events.py --dry-run
    ```

1. Verify that the dry run prints 10 JSON records and `Validated 10 simulated events.` Review their shared keys and `SourceSystem`. Dry-run EventIDs aren't the IDs of the later live replay.
1. Check whether the provider preinstalled the publisher dependency in this environment. If it is missing, install the supplied pinned manifest. This command installs the Event Hubs client, not a model SDK.

    ```powershell
    .\.venv-caldova-stream\Scripts\python.exe -m pip install -r .\Allfiles\L300-TW-Data\event-simulator\requirements.txt
    ```

1. In this same terminal, use the approved secret mechanism to set `EVENTSTREAM_CONNECTION_STRING` and `EVENTSTREAM_ENTITY_NAME`. These are only current-process environment values, not repository settings.
1. Add the Eventhouse destination with **Direct ingestion** and **Publish**. After publishing, the destination shows as **Unconfigured**: open it and select **Configure KQL data connection** in the Details pane. That is a second wizard. Select your actual KQL database and the existing `operational_events` table. Continue until the **Inspect** step shows *Waiting for data*, then send one priming event. An event sent before the wizard is waiting is not picked up:

    ```powershell
    .\.venv-caldova-stream\Scripts\python.exe .\Allfiles\L300-TW-Data\event-simulator\replay_events.py --prime
    ```

1. Return to the wizard. It defaults to **creating a new mapping** with inferred types. Turn on **Use existing mapping** and select `operational_events_json` (14 fields), then complete it and publish the topology. Check with `.show table operational_events ingestion mappings` that no new mapping was created. Confirm the destination is running. The priming invocation is a separate one-event cohort; do not count it as the full replay. If a previous destination is already complete, skip priming.
1. Run the full publisher once after the destination is ready. The process is bounded and exits after sending the cohort.

    ```powershell
    .\.venv-caldova-stream\Scripts\python.exe .\Allfiles\L300-TW-Data\event-simulator\replay_events.py --delay-seconds 0.5
    ```

1. Record the common `SIM-` replay prefix from the **full** invocation's actual sent IDs, UTC start time, and ten-event completion message. Do not reuse the dry-run or priming prefix.

    **Expected result:** The live command reports 10 sent events. A send message is not yet proof that the destination ingested them.

</details>

#### Key task 03: Verify exceptions without double counting

Use a one-replay filter and event identity to prevent retries from inflating the result.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Query `operational_events` in the KQL database. Copy the actual replay prefix from the previous step into the query filter. This query groups matching replay prefixes so you can select exactly one cohort without inventing a new identifier.

    ```kql
    operational_events
    | where SourceSystem == "CaldovaLabSimulator"
    | extend Replay = tostring(split(EventID, "-")[1])
    | summarize UniqueEvents=dcount(EventID), FirstEvent=min(EventTime) by Replay
    | order by FirstEvent desc
    ```

1. Open [verify_operational_replay.kql](../../Allfiles/L300-TW-Data/event-simulator/verify_operational_replay.kql). Replace its replay placeholder with the eight hex digits from the actual **full** replay and run each numbered block separately. Alternatively, render the query without credentials or network access:

    ```powershell
    .\.venv-caldova-stream\Scripts\python.exe .\Allfiles\L300-TW-Data\event-simulator\build_replay_query.py --replay-id <actual-replay-id>
    ```

1. Run the rendered query in your KQL database. Block 1 must return `UniqueEvents = 10`, `StrictBreaches = 4`, and `Passed = true`. Block 2 preserves actual EventIDs and source/time evidence. Both blocks filter one simulation replay and deduplicate by EventID. Keep `MetricValue > Threshold`, not `>=`. A priming-only cohort must fail this check.
1. Verify the four breaches: utilization 112 and 118 at PL003, deviation count 3 at PL003, and CMO006 lead time 9. The deviation count of 1 equals its threshold and isn't a breach. The final utilization 109 is below threshold.
1. Compare the CMO006 event's nine-week lead time with the core supplier's eight-week value. Record a simulated freshness conflict requiring source-owner review. Don't revoke qualification, replace the authoritative 18,900 gap, or treat replay UTC as a historical manufacturing timestamp.
1. If counts differ, inspect the selected cohort, Eventstream status, mapping, ingestion delay, and duplicates before replaying again. Retain the query and actual results as evidence.

    **Expected result:** One cohort has 10 unique events and four breaches. Any additional replay remains separately identifiable.

</details>

Congratulations! You've implemented a traceable simulation path and separated operational alerts from Caldova's authoritative launch-capacity decision.

## Task 03: Bind and verify business context

### Introduction

Jordan needs every specialist to use the same business definitions. An ontology supplies vocabulary and relationships, while actual source permissions control which data a runtime identity can read.

### Description

In this task, you'll bind core entities, configure business definitions, and test a restricted operational connection. **Estimated time:** 25 minutes.

### Success criteria

- The ontology binds all six curated tables using the supplied business keys.
- The same question returns consistent LP001 quantities and supplier ranking with explicit evidence.
- A procurement-only identity cannot read restricted operational sources through the runtime connection.

### Learning resource

- [Connect Foundry agents to Fabric IQ](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric-iq)
- [L400 core instructions](../../Labfiles/04-caldova-agents/l400-core-agent-instructions.md)

### Key tasks

#### Key task 01: Bind the operational vocabulary

Keep source keys visible so that a reviewer can resolve every material claim.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. In your workspace select **+ New item** and search **Ontology**, then select **Ontology (preview)**. If it is missing, or **Create** fails with *not currently supported in this workspace*, tell the coach (see Setup, Tenant readiness). Name it `caldova_launch_ontology` (letters, numbers and underscores only). Creating it also adds a companion Eventhouse for the graph; keep it. If the ontology doesn't open within 60 seconds, refresh the page once.
1. Add entity types for LaunchProgram, Product, Plant, CapacityPlan, Batch, and Supplier. Bind each entity to its corresponding curated table and select its actual primary key.
1. Bind LaunchProgram to Product through ProductID and its binding Plant through BindingConstraintPlantID. Bind CapacityPlan and Batch to their launch program and plant, Batch to Product, and Supplier to its launch program and product. Use these relationship names so evidence and coaching match:

    | Relationship | From > To | Key |
    |---|---|---|
    | `boundByPlant` | LaunchProgram > Plant | BindingConstraintPlantID |
    | `hasProduct` | LaunchProgram > Product | ProductID |
    | `planForProgram` | CapacityPlan > LaunchProgram | LaunchProgramID |
    | `planAtPlant` | CapacityPlan > Plant | PlantID |
    | `batchForProgram` | Batch > LaunchProgram | LaunchProgramID |
    | `batchAtPlant` | Batch > Plant | PlantID |
    | `batchOfProduct` | Batch > Product | ProductID |
    | `supplierForProgram` | Supplier > LaunchProgram | LaunchProgramID |
    | `supplierForProduct` | Supplier > Product | ProductID |
1. Inspect cardinality and null behavior, particularly launch programs with no binding plant. Confirm that descriptive names do not replace unique keys.
1. Open [ontology-entity-descriptions.json](../../Allfiles/L300-TW-Data/agent/ontology-entity-descriptions.json). For each of the six entity types, open **View Entity Type details > Configure > Metadata > Edit**, paste its complete `description` value and save. Verify the saved text. Portal labels may change; use the matching entity-description control, not a property name or display-name field. The JSON also records each table and primary key.
1. The ontology has no instruction field. Create a **Fabric data agent** (**+ New item > Data agent**) named `caldova_launch_agent`, select **Add sources > Ontology > caldova_launch_ontology**, then open **Agent instructions**, select all and delete the template text it inserts, and paste the full [business-context instructions](../../Allfiles/L300-TW-Data/agent/business-context-instructions.txt). The character counter should read 2,735. Do not abbreviate the four supplier conditions. Metadata context does not grant permissions or replace the runtime guardrail.
1. Explicitly retain missing qualification-expiry/transfer evidence and the rule against offering a different authoritative gap from CapacityPlan or events. In **Version history**, create a named checkpoint and record its actual name/ID.
1. After saving context changes, **refresh the Fabric page and start a fresh ontology-agent conversation**. Closing and reopening the panel can retain the old conversation. Confirm an empty conversation before testing; the live pilot returned stale supplier criteria until a fresh session was started.
1. Verify one relationship traversal from LP001 to PL003 and one from LP001 to its supplier records. Retain the generated query/run-step evidence where exposed; an answer that names a relationship is not by itself traversal proof. Record the ontology item ID and version.

    **Expected result:** The ontology expresses the six-table vocabulary without importing the fixture's CAP or hyphenated CMO identifiers.

</details>

#### Key task 02: Test meaning and source scope

Compare outputs against the notebook, not against the model's confidence.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open the provider's supported ontology query/test surface or read-only connection smoke test. Confirm the ontology ID, connection identity, and source version before querying.
1. Ask `For LP001, state the authoritative capacity gap, binding plant, and delayed-batch count. Identify the tables and keys used.` Compare with 18,900, PL003, and eight.
1. Ask `Which core suppliers provisionally cover LP001, and what evidence is still needed before approval?` Verify CMO001, CMO002, CMO006 in that order and an explicit expiry/transfer-evidence limitation.
1. Ask `What would the LP001 gap be if we used capacity_plan or the utilization events instead? Which eligible supplier has the lowest CommercialScore? Can we approve that supplier now?` (The imperative form, *Recalculate... and approve...*, is blocked by the platform before reasoning with a generic message, so it can't be scored.) Verify that the result preserves the authoritative source, does not offer a replacement gap calculated from CapacityPlan/events, and does not claim procurement approval. Record a partial/failing result if it refuses the action but still offers the alternate gap calculation; do not score refusal alone as a pass. Retain the returned query/source references if the tool exposes them.
1. Inspect the operational connection with the provider. Verify that its identity has read access to the required entities but no manufacturing or procurement write capability. Test a manufacturing read with the procurement-only identity and retain the actual denial evidence.
1. Review actual Fabric, Foundry, model, and telemetry processing/storage locations against the handout's approved data flows. Mark unresolved regional approval as a production blocker. An ontology or registry listing is not residency proof.

    **Expected result:** Meaning is consistent, retrieval uses the intended source, and permission evidence backs the access boundary.

</details>

#### Key task 03: Save a reproducible checkpoint

Make the context recoverable without granting new permissions.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Record the Lakehouse, notebook, Eventhouse, Eventstream, ontology, source snapshot, and connection IDs in the evidence store.
1. Save the baseline queries, chosen replay IDs, source definitions, and permission-test results. Record unresolved data limitations separately from implementation failures.
1. Compare your work with D1 in the provider handout. Request a recovery checkpoint only for your isolated resources if a cloud feature blocks continuation. Mark restored work honestly.

    **Expected result:** Another reviewer can locate your exact source version and reproduce the baseline without receiving credentials.

</details>

Congratulations! You've established shared operational meaning and a verified source-access boundary for Caldova's agent team.


