# Caldova governed agents: assets and provider setup

This pack supports a 110-minute Level 300 exercise for developers and platform engineers, with up to 10 minutes of optional challenges. The storyline covers procurement, capacity orchestration, and governance. All business records and supplier names are synthetic.

> **Important**: This repository supplies instructional content, synthetic source files, agent instructions, a deliberately faulty local qualification tool, an instructor solution, and deterministic evaluation checks. It does **not** provision a tenant, import a Copilot Studio solution, deploy a Foundry orchestrator or GitHub Copilot SDK hosted container, configure an ontology, register agents, or create cloud checkpoints. A lab provider must build and verify the integration pack below before this is a runnable hosted workshop. Local Python checks are not evidence that cloud integration works.

## Pack contents

| Asset | Purpose |
|---|---|
| [Exercise](https://github.com/MicrosoftLearning/caip/blob/ad7f3e8361df2f7b44977221461f6c90718b7209/Instructions/Exercises/04-caldova-governed-agents.md) | Learner instructions, eight activities, and three reset points |
| [Agent instructions](agent-instructions.md) | Instructions and tool boundaries for the six agents |
| [Scenario](data/scenario.json) | Baseline, three plants, and six supplier qualification records |
| [Definitions](data/capacity-definitions.md) | Shared business definitions and conflicting legacy identifier |
| [Qualification policy](data/qualification-policy.md) | POL-01 knowledge-base document |
| [Supplier directory](data/approved-suppliers.md) | Procurement-only SharePoint knowledge |
| [RFP tracker](data/rfp-tracker.csv) | Seed for a SharePoint list, not a live connector |
| [Evaluation cases](data/evaluation-cases.jsonl) | Three prompts with deterministic expectations |
| [Qualification tool](Python/qualification-tool/capacity_tool.py) | Local fixture and function-tool business logic |
| [Compliance tool](Python/qualification-tool/gxp_checks.py) | Independent deterministic policy check |
| [Evaluator](Python/qualification-tool/evaluate.py) | Eight checks per exported real run |
| [Instructor solution](Python/qualification-tool/solutions/qualification.py) | Replacement for the intentionally faulty filter |

## Provider readiness gate

Complete this in an isolated training environment. Do not start the workshop with unresolved rows. Record resource URLs, tested versions, a UTC preflight timestamp, and an accountable owner in the learner handout. Never put credentials or access tokens in that handout or this repository.

| Surface | Required preparation | Verification before delivery |
|---|---|---|
| Accounts and permissions | Per-learner lab identities, GitHub Copilot access, Copilot Studio authoring, a Teams test group, Foundry runtime and authoring roles, Fabric source permissions, and scoped agent administration | Each identity can perform its assigned task without a tenant-wide administrative role |
| Licensing and region | Confirm current Agent 365, Copilot Studio, Fabric, hosted-agent, model, and Teams entitlements with the provider. Microsoft 365 Copilot is optional for the Teams route | Record actual tenant and Azure regions, feature availability, consent, quotas, and cross-geo settings. Do not assume a licensing date proves availability |
| Workspace | Provider-supplied working copy of this repository, VS Code, Python 3.13 or later, Git, Azure CLI, and the provider's pinned deployment toolchain | Local baseline tests pass. This pack uses only the Python standard library; cloud harness dependencies must be pinned and separately tested |
| Fabric IQ | Load scenario records, bind ontology entities and definitions, and prepare the three scenario fixtures | CAP-01 maps to N-SF1 and UK-NORTH-01 without double counting. The configured connection identity sees only its permitted evidence |
| Foundry IQ | Index POL-01 and approved SOP context in a restricted knowledge base | CMO Analysis retrieves POL-01 with a resolvable source reference |
| Work IQ and SharePoint | Create a procurement site containing only approved-suppliers and RFP knowledge. Import the CSV into an RFP list | Procurement agent and Alex's identity cannot retrieve the restricted plant or batch source through another connection |
| Procurement action | Supply an imported agent flow named RecordFollowUp with rfp_id, request_text, and client_request_id inputs | Validate an open RFP against the list; append a FollowUpRequests item with receipt_id, RFP ID, requested_by, requested_at, request_text, and client_request_id. A repeated request ID returns the existing receipt. No write permission to qualification data |
| Foundry agent team | Deploy a code-backed Capacity Decision Orchestrator plus Current Capacity, CMO Analysis, COO Recommendation, and Compliance Guardrail | Orchestrator invokes the four specialists, enforces the guardrail in code, and exposes actual tool calls and identity correlation. A published prompt that only describes orchestration is insufficient |
| Qualification function | Supply an authenticated AssessCandidates adapter that calls capacity_tool.assess with the selected scenario; package policy.py and qualification.py from the learner working copy | Before repair it proposes CMO-02, CMO-03, CMO-01. After repair it proposes only CMO-01. Reject unknown scenario IDs and do not let prompts select arbitrary files |
| Hosted guardrail | Supply a container built with a verified GitHub Copilot SDK sample, an actual Copilot SDK session and registered gxp-checks tool, managed model authentication, and access-controlled audit storage | The SDK harness invokes the deterministic tool; runtime code uses that tool's verdict. No static GitHub token or model API key in learner files. The container and startup command are not included in this pack |
| Hosted deployment handout | Give learners the exact tested deployment command, working directory, configuration-file path, image tag or digest, identity, log URL, and rollback command for that container | A learner can deploy an isolated revision, invoke it, identify the SDK harness and tool span, and restore the previous revision. Do not invent a generic deploy command |
| Copilot Studio connection | Prepare a supported new-Foundry agent ID, project endpoint, connection consent, and an enabled Activity protocol endpoint | An authenticated end-to-end call from Copilot Studio succeeds. Activity enablement is programmatic; a Responses endpoint alone is not sufficient |
| Teams | Enable the lab group's published Procurement Desk and allow the required app | One group member can invoke the agent. A user outside the group cannot activate it |
| Agent 365 and identities | Prepare the supported integration and registry entries for six logical agents, owners or sponsors, and actual runtime identity mapping | Match registry/application/agent identity IDs using the provider's identity map. These IDs are not interchangeable. Do not assume internal helper agents automatically appear in the tenant registry |
| Governance fault | Seed a harmless, isolated Unapproved CMO Scraper with no live public crawler or manufacturing access | A learner can block it and confirm denial after propagation; nobody else depends on it |
| Observability | Enable Foundry traces and appropriate identity, activity, and audit logs | Correlate a Teams request to orchestration, guardrail verdict, candidate-tool version, agent IDs, and actual data-access records. Registry metadata alone is not a data-access log |
| Evaluation | Prepare agent evaluation permissions, a judge model, the three isolated fixtures, and the structured export adapter | Actual agent runs supply messages and tool traces for built-in evaluators. evaluate.py receives the result contract below and real registry evidence; do not feed answer keys to the agent |

Use the [hosted-agent quickstart](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/quickstart-hosted-agent), [hosted-agent concepts](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents), [Fabric IQ tool guide](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric-iq), and [Copilot Studio connection guide](https://learn.microsoft.com/en-us/microsoft-copilot-studio/add-agent-foundry-agent) to build this integration. Follow the connection's current authentication requirements, including delegated consent where applicable. A prompt refusal is not an authorization test.

If a capability cannot be provided, prepare a labeled walkthrough with screenshots, recorded inputs and outputs, and real redacted trace evidence. The learner records it as **observed**, not **implemented**. No such recording or cloud checkpoint is supplied in this repository. Keep the product's role in the storyline, but do not claim a walkthrough proves a working integration.

## Checkpoints and reset contracts

Prepare separate per-learner copies. Restore only the learner's own resources. Checkpoints contain synthetic business data and configuration, never reusable user tokens.

| Checkpoint | Start here | State that the provider must restore | Smoke test |
|---|---|---|---|
| C0 - Context ready | Part 1 | Data, ontology, knowledge bases, flow, empty Procurement Desk, Foundry starter team, hosted guardrail deployment package | Source records resolve; procurement source access is restricted |
| C1 - Procurement ready | Part 2 without Part 1 | C0 plus tested Procurement Desk, approved SharePoint knowledge, follow-up action, and Teams publication | RFP-01 and RFP-02 are visible; one test follow-up returns a receipt |
| C2 - Runtime ready | Part 3 without Part 2 | C1 plus connected five-agent Foundry workflow, SDK guardrail, deliberate filter defect, six registered logical agents, test scraper, and captured failure trace | External scenario is blocked by the guardrail because CMO-02 and CMO-03 lack valid qualification evidence |
| C3 - Validated | Instructor recovery or demonstration | Repaired filter deployed and three real evaluation runs with evidence exports | Standard and internal-only cases pass policy; conflict case returns Needs review |

Restoring C2 must restore the deliberately faulty qualification.py without weakening policy.py or changing supplier evidence. The post-repair version must not retain an old loaded module or container layer. Record a new function version or image digest and confirm that the next trace uses it.

## Expected decisions

The frozen clock makes this exercise reproducible after 2026. Use calendar-day transfer arithmetic. Expiry must cover the launch date, not just the decision date.

| Scenario | Internal additional units | Remaining gap | Expected result after repair |
|---|---:|---:|---|
| external-support | 4,500 | 2,500 | Only CMO-01 is eligible. Its 3,000 units cover the gap; transfer completes October 31, 2026. Recommend procurement and quality review, not automatic award |
| internal-sufficient | 7,500 | 0 | No external CMO recommendation. Guardrail still runs |
| conflicting-evidence | Unknown | Unknown | Identify CAP-01 versus LEG-01, return Needs review, and request data-owner resolution |

`load_scenario` creates the latter two fixture variants. The provider must expose the same isolated fixture selection to the actual runtime. Before repair, the local candidate tool's cost-sorted shortlist is CMO-02, CMO-03, CMO-01. The independent guardrail blocks release of that shortlist. CMO-04 fails UK location, CMO-05 fails readiness, and CMO-06 lacks an audit reference. A refusal to release the bad draft is the intended initial failure, not a failure of the guardrail.

## Local Python validation

In a terminal at Python/qualification-tool, use the following commands. They do not invoke cloud agents or require Azure authentication.

```powershell
python -m unittest discover -s tests -p test_baseline.py -v
python -m unittest discover -s tests -p test_evaluation.py -v
python -m unittest discover -s tests -p test_regression.py -v
```

The first two commands pass with the starter. The regression command deliberately fails two tests. After the learner repairs qualification.py, `python -m unittest discover -s tests -v` must pass. An instructor can copy solutions/qualification.py over qualification.py in an isolated working copy to recover. Do not ship the solution as the defective checkpoint.

Use the following commands to reproduce the candidate tool and independent check. The compliance command returns exit code 1 before repair and 0 after repair.

```powershell
python capacity_tool.py --case external-support --output results\proposal.json
python gxp_checks.py --proposal results\proposal.json --output results\guardrail.json
```

Local files contain the deterministic business fields only. They are not proof that a Copilot SDK session ran or an Agent 365 audit record was written.

## Verified local behavior

The pack's local tools were checked with Python 3.14.5. The starter passes nine baseline tests and eight evaluator tests, with exactly two intentional regression failures. In an isolated copy with the instructor repair applied, all 19 tests pass. CLI checks confirm the blocked starter shortlist, the corrected CMO-01-only shortlist, the internal-only case, and the safe rejection of conflicting evidence. The evaluator CLI accepts all 24 expected criterion results and rejects an unsupported CMO result.

These checks use synthetic local fixtures and test-only trace metadata. They do not certify a hosted Copilot SDK package, a Foundry-to-Copilot Studio connection, Agent 365 registration, or a cloud evaluation. Those remain provider preflight tests.

## Runtime output and evaluation contract

The provider's orchestrator returns a readable answer and a structured record. Its export adapter adds authenticated runtime metadata, not model-supplied assertions about execution. Write one JSON object per real run to `results/agent-results.jsonl`. Required fields are:

| Field | Type and meaning |
|---|---|
| case_id | One of the three supplied case IDs |
| status | Ready for review or Needs review |
| internal_units, remaining_units | Integer units, or explicit null for the conflict case |
| eligible_cmo_ids | Array of all eligible external CMO IDs, empty for internal-only or unresolved cases |
| facts, assumptions, gaps | Arrays of strings. Facts must be nonempty; gaps must be nonempty for conflict |
| next_action | Nonempty, specific next action for Peter |
| claims | Nonempty array of objects with text and nonempty evidence_ids arrays. Cite material capacity, qualification, and policy claims |
| guardrail | Object containing ran and passed booleans and policy_id. Conflict requires ran=true, passed=false, and POL-01 |
| trace | Object containing real run_id, actual invoked agent_ids, guardrail_before_final boolean, and blocked_agent_called boolean, derived from verified traces |

Create `results/registry.json` from real registry and identity evidence as a JSON array with `agent_id`, `name`, `owner`, and `blocked` for each unique runtime identity. Use the six exact names in agent-instructions.md. Normalize duplicate publishing lifecycle rows with the identity map, not by hiding distinct agents. A registry record ID is not necessarily the runtime Entra identity ID. The extra scraper record may be included with blocked=true; it must never appear in a run's invoked IDs.

The following command applies eight deterministic checks to each of the three real results. All 24 checks must pass. Missing, duplicate, or extra evaluation cases are an error, not a partial success.

```powershell
python evaluate.py --results results\agent-results.jsonl --registry results\registry.json --output results\scorecard.json
```

`score` is a plain Python custom rubric, not an automatically registered Foundry evaluator. If the provider exposes it inside Foundry, build and verify the registration adapter against the current evaluation SDK. Otherwise run it locally beside the Foundry evaluation and retain both artifacts. The rubric checks field values, evidence-ID coverage, and exported control metadata. A person must still verify that citations support the claims and that the exported trace and identity evidence are authentic.

In Foundry, run Task Adherence, Tool Call Accuracy, and Groundedness when supported for the selected agent target and dataset. Supply actual conversation/tool messages and retrieved grounding context through the current evaluator field mappings. Do not upload this answer-key JSONL unchanged and expect tool-call metrics to work. Set and record the built-in evaluators' thresholds before running. Treat a missing metric as Not evaluated, not Pass. Retain the real per-case results and inspect failed examples. A passed deterministic rubric never substitutes for a missing built-in evaluation.

## Data handling and cleanup

The UK manufacturing-location fixture is a policy input, not an assertion about product residency. Validate tenant location, Foundry project processing region, Fabric processing and storage, SharePoint location, model deployment, telemetry storage, SDK data flows, and cross-geo settings separately. Have the customer validate GxP controls and electronic-record requirements before production use.

Before delivery, test a complete cleanup in a disposable learner environment. Learners remove only their own Teams publication, test follow-ups, agent revisions, and dedicated Azure resources. Administrators restore scoped availability and the test scraper state. Never delete a shared tenant, shared resource group, or another learner's agent. Purge local run exports according to training retention policy. Preserve required evidence only in the approved training store.
