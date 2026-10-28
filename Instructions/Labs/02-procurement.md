---
lab:
    title: 'Build the Caldova procurement entry point'
    description: 'Implement procurement knowledge, safe follow-up actions, and scoped Teams access.'
    level: 400
    duration: 60
    islab: true
---

# Exercise 02: Build the procurement entry point

## Scenario

Alex needs a business-owned agent for supplier contacts and RFP follow-up. It must not read unrestricted manufacturing data or imply that a procurement directory proves supplier qualification. You build this interaction separately from the technical decision runtime.

## Objectives

After you complete this exercise, you'll be able to:

- Configure a Copilot Studio agent with approved procurement sources and explicit delegation boundaries.
- Add an append-only follow-up action and verify confirmation and idempotency.
- Publish to the assigned Teams audience and test permitted and denied access.

## Duration

**Estimated time:** 60 minutes

## Before you begin

Use your completed Exercise 01 environment or the provider's D1 checkpoint. Keep the synthetic procurement RFP identifiers separate from core supplier identifiers unless the provider supplies a reviewed crosswalk. The decision service is connected in Exercise 03, not during this exercise.

# Task 01: Configure procurement knowledge and boundaries

## Introduction

Alex needs a reliable view of supplier contacts and RFP status. Procurement knowledge doesn't establish manufacturing qualification, and the agent must not gain broad operational access merely because Alex can author it.

## Description

In this task, you'll create Procurement Desk, attach approved knowledge, and test citations and refusal behavior. **Estimated time:** 25 minutes.

## Success criteria

- Procurement Desk answers an open-RFP question using resolvable procurement citations.
- It has only the approved supplier directory and RFP knowledge sources.
- It reports an unavailable decision service rather than inventing a capacity answer.

## Learning resource

- [Procurement agent instructions](../../../../Labfiles/04-caldova-agents/agent-instructions.md)
- [Supplier directory](../../../../Labfiles/04-caldova-agents/data/approved-suppliers.md) and [RFP seed](../../../../Labfiles/04-caldova-agents/data/rfp-tracker.csv)

## Key tasks

### Key task 01: Create the business-owned entry point

Keep the agent's purpose narrow until the governed decision service is connected.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open [Copilot Studio](https://copilotstudio.microsoft.com) with the assigned procurement authoring identity and select the isolated training environment from the provider handout.
1. Create an agent named `Caldova Procurement Desk` in your assigned solution or use the empty learner-specific starter. Record its actual ID so display-name duplication doesn't confuse later registry matching.
1. Apply the `Caldova Procurement Desk` instructions from `Labfiles\04-caldova-agents\agent-instructions.md`. Don't apply the fixture's capacity instructions to the procurement agent.
1. Review the provider-approved authentication settings. Preserve user/source authorization and don't enable anonymous access as a shortcut.
1. Save the agent. Confirm that it currently has no connected Foundry agent, manufacturing connector, public crawler, or broad organizational knowledge source.

    **Expected result:** The agent is scoped to procurement and cannot yet claim to execute a capacity decision.

</details>

### Key task 02: Ground answers in approved procurement sources

Use the prepared SharePoint items, not a local file attachment mistaken for a live governed source.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open the prepared procurement SharePoint site from the handout. Locate the approved supplier directory and RFP list seeded from the supplied assets. Verify RFP-01 and RFP-02 and their current status in the actual list.
1. Add only these approved procurement sources to the agent's **Knowledge** configuration. Confirm the source access identity and wait for indexing/readiness as required by the supported connector.
1. Test `Which RFPs are open, and who should Alex contact? Cite the RFP and supplier records.` Open the citations and compare the answer with the source list.
1. Test `Does being in the supplier directory prove that a supplier is qualified for manufacturing?` Verify that the answer distinguishes directory membership from quality approval.
1. Inspect the core supplier IDs alongside the procurement fixture IDs. Confirm that the agent doesn't equate `CMO001` and `CMO-01` or claim RFP-01 belongs to the top core supplier without an approved crosswalk.

    **Expected result:** Answers have correct procurement references and no inferred manufacturing qualification or cross-profile mapping.

</details>

### Key task 03: Verify the access and delegation boundary

A refusal is useful only when permissions also prevent the underlying access.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Ask `Show me the raw plant and batch records behind the launch gap.` Verify that Procurement Desk does not disclose restricted records.
1. Use the provider's authorized source-access test with the same procurement-only identity. Retain the actual denied read and inspect whether any alternate connection bypasses the restriction.
1. Ask `Can Caldova close the 7% launch-capacity gap internally?` Verify that the agent reports the decision service is not connected. Don't accept a plausible answer from model memory.
1. Save the agent version, source IDs, citation check, and denied-access evidence. Record a defect if it can read the restricted source even when its prompt says it cannot.

    **Expected result:** Procurement data is useful, manufacturing access remains restricted, and the unavailable runtime is reported explicitly.

</details>

Congratulations! You've built Alex's procurement entry point without using prompt instructions as a substitute for source authorization.

# Task 02: Implement and test follow-up actions

## Introduction

Alex should be able to record an RFP follow-up without changing supplier qualification. A retry must not create duplicate work or a fabricated success receipt.

## Description

In this task, you'll bind the prepared append-only action and test confirmation, idempotency, and invalid requests. **Estimated time:** 20 minutes.

## Success criteria

- A confirmed open-RFP request creates one real FollowUpRequests item and receipt.
- Repeating the same client request ID returns the existing receipt without a duplicate.
- A rejected or failed request creates no new item and doesn't claim success.

## Key tasks

### Key task 01: Bind the approved action

Use the supplied flow contract rather than granting general list-edit permissions.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open **Tools** for Procurement Desk and add the provider-prepared `RecordFollowUp` agent flow.
1. Map `rfp_id`, `request_text`, and `client_request_id` to the flow's actual inputs. Inspect its receipt result and error path.
1. Review the flow with the provider: it validates an open RFP and appends a FollowUpRequests item with receipt ID, RFP ID, requester, UTC timestamp, request text, and client request ID.
1. Verify that its connection cannot update supplier qualification or manufacturing records. Confirm that duplicate client IDs return the existing item rather than executing another write.
1. Save the tool configuration and confirm that agent instructions require the requester to identify an RFP and confirm the follow-up before execution.

    **Expected result:** The action's write boundary is append-only and independently enforced.

</details>

### Key task 02: Test confirmation and safe retry

Use an unused request ID for your learner so another learner's existing receipt doesn't mask a failed write.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Select an open RFP from your actual list. Ask the agent to record a follow-up for RFP-01 requesting launch-window availability, using a client request ID formed from your assigned learner alias plus `-FOLLOWUP-01`.
1. Withhold confirmation first. Verify no FollowUpRequests item is added. Then confirm the same requested action.
1. Open the actual list and verify one new item, its requester, RFP reference, timestamp, request text, and receipt. Match the receipt to the agent result.
1. Submit the identical confirmed request with the same client request ID. Verify the existing receipt is returned and the item count doesn't increase.
1. Save the action trace, receipt reference, and before/after counts in the approved evidence store. Exclude sensitive request text if the provider's evidence policy requires it.

    **Expected result:** One approved action produces one item, and a retry doesn't duplicate it.

</details>

### Key task 03: Test rejection without false success

Invalid input and tool errors must remain visible to the requester.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Ask for a follow-up against a nonexistent RFP ID with a new client request ID. Verify rejection and no new item.
1. Ask the agent to mark a supplier qualified through this flow. Verify it has no such tool capability and creates no follow-up as a substitute unless you separately request and confirm one.
1. Use the provider's isolated flow-failure test, if supplied, and verify an explicit failure response with no fabricated receipt. If no safe failure test exists, mark that test **Not run**.
1. Record the expected rejection separately from an unexpected tool failure. Keep both in the action acceptance matrix.

    **Expected result:** The agent reports what actually occurred and never substitutes a success-shaped answer for a failed write.

</details>

Congratulations! You've enabled a practical procurement action with confirmation, idempotency, and a narrow write boundary.

# Task 03: Publish and verify audience access

## Introduction

A test-pane success doesn't prove that Alex can use the published agent or that unrelated users are excluded. You test the actual business channel and its audience.

## Description

In this task, you'll publish Procurement Desk to the assigned Teams group and verify positive and negative access. **Estimated time:** 15 minutes.

## Success criteria

- An authorized Teams user can invoke the published agent and open its procurement citations.
- An out-of-group test user cannot activate the agent under the assigned availability policy.
- Published version and audience evidence are recorded without confusing activation with source authorization.

## Learning resource

- [Publish an agent to Teams](/microsoft-copilot-studio/publication-add-bot-to-microsoft-teams)

## Key tasks

### Key task 01: Publish to the training audience

Use the provider-approved publication path and don't make the agent organization-wide.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Review the agent's knowledge and action configuration, then select **Publish**. Record the published version and UTC time.
1. Open **Channels** > **Teams and Microsoft 365 Copilot** and use the provider-approved installation/publication route for the isolated tenant.
1. Restrict availability to the prepared `Caldova Launch Team` group using the provider's supported administration surface. Obtain scoped administrator approval if required.
1. Install or open the agent in Teams with the in-group test identity. Verify the name and published revision rather than testing an older installation.

    **Expected result:** The published entry point is available only through the approved training channel and audience configuration.

</details>

### Key task 02: Validate the published experience

Test the same boundaries outside the authoring pane.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Ask the open-RFP question from Teams. Verify the cited records and confirm the response comes from Procurement Desk.
1. Ask the launch-capacity question again. Verify that the decision service remains explicitly unavailable until Exercise 03 connects it.
1. Test activation with the provider's out-of-group identity after policy propagation. Capture the actual denial or unavailability result. Don't infer a denial solely from a missing search result.
1. Verify that channel activation hasn't changed manufacturing-source access. Keep audience access and source permissions as separate acceptance rows.
1. Save the publication ID/version, audience assignment, authorized interaction, and denied activation. Keep the agent deployed for the next exercise.

    **Expected result:** Teams behavior matches the published configuration, and access boundaries remain intact.

</details>

Congratulations! You've delivered a scoped business interface ready to connect to Caldova's governed technical runtime.

### Key task 03: Test rejection without false success

Invalid input and tool errors must remain visible to the requester.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Ask for a follow-up against a nonexistent RFP ID with a new client request ID. Verify rejection and no new item.
1. Ask the agent to mark a supplier qualified through this flow. Verify it has no such tool capability and creates no follow-up as a substitute unless you separately request and confirm one.
1. Use the provider's isolated flow-failure test, if supplied, and verify an explicit failure response with no fabricated receipt. If no safe failure test exists, mark that test **Not run**.
1. Record the expected rejection separately from an unexpected tool failure. Keep both in the action acceptance matrix.

    **Expected result:** The agent reports what actually occurred and never substitutes a success-shaped answer for a failed write.

</details>

Congratulations! You've enabled a practical procurement action with confirmation, idempotency, and a narrow write boundary.

