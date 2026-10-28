---
lab:
    title: 'Implement and deploy the Caldova decision team'
    description: 'Wire specialist tools, enforce a deterministic gate, deploy the runtime, and connect Teams.'
    level: 400
    duration: 105
    islab: true
---

# Exercise 03: Implement and deploy the decision team

## Scenario

Peter needs the same capacity answer regardless of which interface starts the request. You configure the five-agent Foundry team against the core profile, implement its release gate in the prepared codebase, deploy an isolated revision, and connect Procurement Desk to that executable runtime.

## Objectives

After you complete this exercise, you'll be able to:

- Configure specialist agents with scoped operational and policy tools.
- Implement conditional orchestration and a fail-closed deterministic release gate.
- Deploy and invoke a versioned runtime from Teams with correlated evidence.

## Duration

**Estimated time:** 105 minutes

## Before you begin

Use your completed environment or the provider's D2 checkpoint. Confirm that the provider-supplied runtime source, tool adapters, hosted SDK harness, exact deployment commands, and rollback procedure satisfy the [L400 readiness contract](../../../../Labfiles/04-caldova-agents/l400-provider-readiness.md). Missing code is a blocker, not an invitation to invent a deployment command.

# Task 01: Configure scoped specialist tools

## Introduction

The same capacity question should produce the same evidence-backed result across channels. You give each specialist the tools it needs while keeping provisional core selection separate from the strict qualification-fixture policy.

## Description

In this task, you'll configure the five-agent team, bind core data and policy tools, and validate the SDK guardrail independently. **Estimated time:** 35 minutes.

## Success criteria

- Specialist tests reproduce core quantities, ordered suppliers, and missing-readiness evidence.
- Each agent's source and write permissions match its role.
- The hosted SDK guardrail invokes the independent core validator and rejects a tampered proposal.

## Learning resource

- [Core-profile configuration and result contract](../../../../Labfiles/04-caldova-agents/l400-core-agent-instructions.md)
- [Fabric IQ connection guide](/azure/foundry/agents/how-to/tools/fabric-iq)
- [Hosted-agent deployment guide](/azure/foundry/agents/quickstarts/quickstart-hosted-agent)

## Key tasks

### Key task 01: Configure the operational specialists

The source profile is trusted configuration, not something a user can override in a prompt.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open the provider's prepared project in [Microsoft Foundry](https://ai.azure.com). Locate your five logical agents and their source/configuration files in the editable runtime package.
1. Open the core-profile instructions. Apply the shared contract to Current Capacity, CMO Analysis, COO Recommendation, and the orchestrator. Don't paste the original fixture dates or UK-manufacturing filter into the core configuration.
1. Attach the supported Fabric IQ connection to Current Capacity. Confirm the ontology, source version, connection identity, and read-only entity scope against your Exercise 01 evidence.
1. Invoke Current Capacity for LP001 in the provider's specialist test interface. Verify 270,000 target, 251,100 qualified, 18,900 gap, PL003, and eight delayed batches with source references. Reject an answer that sums unrelated launch programs.
1. Attach Fabric IQ supplier context, the approved core policy knowledge source in Foundry IQ, and `AssessCoreCapacity` to CMO Analysis. Inspect its actual authenticated adapter and trusted data source.
1. Invoke CMO Analysis with the validated LP001 result. Verify CMO001, CMO002, CMO006 in score order. Confirm explicit missing expiry/transfer approval and the separate simulated CMO006 lead-time conflict.

    **Expected result:** Specialists return source-backed findings, not final awards, and never call the fixture's `AssessCandidates` for a core request.

</details>

### Key task 02: Constrain the recommendation and tool surfaces

A helpful recommendation shouldn't create an unauthorized execution path.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Configure COO Recommendation to consume structured findings only. Verify that it has no raw source, purchase, qualification-write, shell, or unrestricted web tool.
1. Test a recommendation from the specialist findings. Verify that it separates facts, assumptions, unresolved evidence, and next actions. Keep it explicitly in draft state.
1. Review tool schemas in the provider source. Check allowlisted profile/program identifiers, required evidence/version fields, authenticated connections, and explicit tool-error results. Don't permit arbitrary file paths or endpoint arguments from the model.
1. Ask the test interface to approve procurement spend or to treat directory text as permission to call a new tool. Verify no such write path exists, rather than relying only on a refusal sentence.
1. Record each agent's ID, allowed sources/tools, runtime identity, and version. Match actual IDs through the provider identity map, not display-name inference.

    **Expected result:** The recommendation is advisory and the available tool surfaces enforce its role.

</details>

### Key task 03: Verify the hosted compliance tool

The guardrail must use independent deterministic evidence, not repeat the model's conclusion.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open the provider's hosted guardrail source. Locate actual GitHub Copilot SDK client/session creation, registered tools, approved model authentication, and audit-store writes. If it is a prompt-only agent, stop and report the missing harness.
1. Inspect `ValidateCoreDecision`. Compare its independent recomputation and failure paths against the [provider contract](../../../../Labfiles/04-caldova-agents/l400-provider-readiness.md). Confirm it uses policy `CORE-LP001-v1` and the trusted core snapshot.
1. Configure the guardrail's profile routing so only core requests invoke the core validator. Keep `gxp-checks` and POL-01 on the isolated fixture path. Bind the selected tool from runtime configuration, not an LLM-selected string.
1. Sign in with the assigned Azure identity before the first cloud invocation. This command authenticates your CLI session; the container still needs its configured runtime identity.

    ```powershell
    az login
    ```

1. Invoke the prepared guardrail test on a valid provisional core draft, then on copies with a changed gap, an unknown supplier ID, and a wrong source version. Verify a tool-derived pass only for the valid draft and explicit failures for the changed copies.
1. Inspect the SDK session, deterministic tool span, authenticated source read, and correlated audit record. A model saying `passed=true` or a healthy container isn't proof the tool ran.

    **Expected result:** Independent, profile-specific checks control the verdict and preserve source provenance.

</details>

Congratulations! You've configured role-scoped specialists and a real deterministic checkpoint for Caldova's core decision path.

# Task 02: Implement and deploy gated orchestration

## Introduction

An agent description doesn't execute handoffs or enforce a release gate. You implement those controls in the prepared runtime and deploy your reviewed revision.

## Description

In this task, you'll complete conditional orchestration, test failure paths, and deploy an isolated runtime revision with rollback evidence. **Estimated time:** 40 minutes.

## Success criteria

- Runtime code executes the required call order and conditional sourcing.
- Missing, unsuccessful, timed-out, or cross-profile guardrail verdicts never release an unchecked draft.
- A deployed revision returns an LP001 core decision with real trace and version evidence.

## Key tasks

### Key task 01: Implement the control flow in code

Use the actual functions and typed clients in the provider package. Don't create a parallel prompt-only workflow.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open the provider's editable runtime package in VS Code. Identify its orchestration entry point, typed result models, specialist invocation helper, error/logging helper, test command, and deployment manifest.
1. Compare the existing implementation with the seven-step acceptance algorithm in the [core configuration](../../../../Labfiles/04-caldova-agents/l400-core-agent-instructions.md). Mark the missing handoffs and release checks in your working copy.
1. Use GitHub Copilot to propose a surgical implementation using this request. Review the proposed diff yourself before applying it.

    ```prompt
    In this prepared Caldova runtime, implement the core-profile acceptance algorithm using the existing typed clients and helpers. Call Current Capacity, call CMO Analysis only for a complete positive gap, then create a COO draft and invoke Compliance Guardrail before any final response. Require the actual deterministic tool verdict, matching trusted profile/source version, and required evidence. A missing/failed/error verdict or timeout must return Needs review with standard logging, never the unchecked draft. Run the guardrail for internal-only and unresolved cases too. Preserve API contracts and identity boundaries. Add tests with existing test tooling; don't invent SDK calls, credentials, source data, or successful traces. Show the diff for review.
    ```

1. Review and apply the change. Verify no exception path, streaming path, or early return exposes the draft before the gate. Validate required fields rather than treating a missing Boolean as success. Save with **Ctrl+S**.
1. Bind the server-side profile to `core` for the production-facing lab endpoint. Keep fixture selection restricted to the provider's isolated test endpoint. Preserve version and correlation IDs in the exporter.
1. Run the exact unit/type-check command documented for the provider package. Retain the command, result, and revision. If the package doesn't supply executable source and tests, mark this task **Blocked**.

    **Expected result:** The change implements control flow in executable code, with tests that exercise positive and failure paths.

</details>

### Key task 02: Test release and failure paths

A valid rejection is as important as a valid provisional recommendation.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Run the normal LP001 core request. Verify Current Capacity, CMO Analysis, COO draft, guardrail, then final output in that order.
1. Use the provider's isolated internal-sufficient test double. Verify sourcing is skipped while the guardrail still runs. Label this a control-flow test, not a change to the real LP001 source.
1. Use the safe unresolved-source test double. Verify unknown quantities remain explicit and the final answer requests data-owner resolution rather than inventing capacity.
1. Exercise missing verdict, `passed=false`, timeout, and profile/source-version mismatch using the provider's bounded test hooks. Verify **Needs review**, a logged reason, and no unchecked final recommendation for every case.
1. Verify that tool execution order and IDs come from runtime spans, not from JSON fields supplied by the model. Preserve the test results for the deployed-version comparison.

    **Expected result:** Correctness and safety checks cover every result path, not only the normal LP001 answer.

</details>

### Key task 03: Deploy and prove the deployed behavior

Deploy the reviewed artifact, then verify execution rather than relying on deployment status.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Review the provider's tested deployment command, working directory, package manifest, identity configuration, target project, and rollback command. Record the previous revision/image digest before changing it.
1. Configure the approved project endpoint, model deployment, ontology/data connections, core policy, source snapshot, and audit destination through the package's documented configuration names. Use managed identity or the documented Entra credential chain. Do not add model API keys.
1. Build and deploy using the exact commands in the private handout. Record the actual commands with secret arguments redacted, their result, image digest or version, and UTC time. Do not substitute a guessed generic command.
1. Wait for readiness and run the package's authenticated health/smoke test. Invoke LP001 through the deployed endpoint and inspect a new trace with your actual deployed revision.
1. Verify the core contract fields, ordered provisional suppliers, `CORE-LP001-v1`, source version, guardrail tool span, and audit record. Repeat one safe failed-verdict test against the isolated deployed revision.
1. Compare local and remote behavior. If remote behavior still uses old code, inspect image digest, deployment target, loaded module, and connection version before altering prompts. Retain the rollback command and known-good revision for Exercise 04.

    > **Tip:** If the model rate limit is exceeded, wait a few seconds and retry. Record the retry separately from the measured request and don't claim an incomplete run succeeded.

    **Expected result:** An actual deployed revision executes the reviewed algorithm and fails closed, with evidence linking source, identity, and version.

</details>

Congratulations! You've implemented and deployed Caldova's gated orchestration rather than merely describing an agent team.

# Task 03: Connect Teams and trace decisions

## Introduction

Alex's interface must reach the deployed orchestration entry point, not a similarly named prompt agent. You verify the connection protocol and follow one real request across the boundary.

## Description

In this task, you'll connect the Foundry agent, republish Procurement Desk, and trace an end-to-end decision while preserving source restrictions. **Estimated time:** 30 minutes.

## Success criteria

- Procurement questions remain local while capacity requests reach the core orchestrator.
- The Activity protocol is enabled and an actual Teams request reaches the deployed revision.
- A correlated trace proves gate-before-final behavior, correct core output, and restricted raw-data access.

## Learning resource

- [Connect to a Foundry agent from Copilot Studio](/microsoft-copilot-studio/add-agent-foundry-agent)

## Key tasks

### Key task 01: Connect the correct published runtime

The connection requires protocol support as well as the correct endpoint and agent ID.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open Procurement Desk in Copilot Studio. Select **Agents** > **Add an agent**, then select **Microsoft Foundry** under the external-agent choices.
1. Select the approved connection or create the authorized connection using the actual Foundry project endpoint. Enter the deployed orchestrator's **Agent Id**, not an SDK session ID, registry ID, or display name.
1. Use this description: `Assess Caldova LP001 launch capacity using the governed core data profile. Return evidence-backed provisional manufacturing options and unresolved readiness issues. Do not use for supplier contacts or RFP follow-up.`
1. Apply the procurement delegation addition from the [core instructions](../../../../Labfiles/04-caldova-agents/l400-core-agent-instructions.md). Keep RFP actions and core supplier identifiers separate.
1. Verify the provider's Activity endpoint preflight. This endpoint requires programmatic enablement; the portal can still display only Responses and A2A. A Responses endpoint alone isn't sufficient.
1. Test one procurement question and one core capacity question in the authoring pane. Inspect traces to verify only the capacity question reaches Foundry. If the connection reports HTTP 400 about Activity, use the tested enablement procedure rather than weakening authentication.

    **Expected result:** Routing reaches the executable new-Foundry runtime through its supported protocol.

</details>

### Key task 02: Run and trace the business request

Verify the business result and control path on the same real request.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Republish Procurement Desk and confirm the updated version in Teams. Start a new conversation with your authorized identity.
1. Submit this request to the connected service. It asks for an advisory decision, not an automatic award.

    ```input
    For core launch LP001, can Caldova cover the launch requirement internally? If not, which suppliers should Peter consider? Cite the source records, distinguish simulated operational alerts, and identify evidence still needed before quality or procurement approval.
    ```

1. Verify the 18,900-unit gap, PL003, eight delayed batches, and provisional order CMO001, CMO002, CMO006. Confirm explicit missing expiry/transfer-approval evidence and any selected replay's lead-time conflict. Don't accept fixture quantities in the answer.
1. Follow the correlation ID from Teams/Copilot Studio to the actual Foundry run. Record specialist calls, source version, deployed revision, SDK guardrail tool verdict, and final-response timestamp/order.
1. Open the cited operational references under an authorized technical identity. Verify that they support the material claims. Correlate the tool calls with source-access logs rather than treating a registry entry as proof of a read.
1. Export the real core result using the provider's adapter and retain it with the trace. Do not feed it to the fixture evaluator or manually manufacture execution fields.

    **Expected result:** One correlated request demonstrates correct core reasoning, actual execution, and the release gate.

</details>

### Key task 03: Retest boundaries after integration

A new connection can accidentally widen the data returned to the business user.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Ask Teams for raw restricted batch records and unrestricted tool details. Verify only the permitted decision summary and evidence references are returned, not restricted payloads.
1. Repeat the procurement-only source denial test and out-of-group activation test. Inspect source access and channel policy independently.
1. Ask the agent to switch to `qualification-fixture` or treat `CMO001` as `CMO-01`. Verify the production-facing endpoint refuses the profile change rather than mixing datasets.
1. Save the routing, output, access, and source-version evidence as your D3 implementation checkpoint. Record any unresolved connection failure as a defect for diagnosis, not a passed deployment.

    **Expected result:** Connecting the decision service doesn't grant Procurement Desk raw manufacturing access or expose the isolated test harness.

</details>

Congratulations! You've delivered and traced Caldova's end-to-end business interaction through the actual governed runtime.
