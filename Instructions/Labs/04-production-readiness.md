---
lab:
    title: 'Troubleshoot and validate the Caldova agent solution'
    description: 'Repair implementation faults, measure an optimization, and assess production-readiness evidence.'
    level: 400
    duration: 120
    islab: true
---

# Exercise 04: Troubleshoot, optimize, and validate

## Scenario

The first deployment is not the finish line. Jordan must diagnose a deliberately faulty qualification filter, prove that the deployed repair ran, isolate a cross-service incident, and show that an optimization doesn't weaken correctness or governance.

## Objectives

After you complete this exercise, you'll be able to:

- Reproduce a code defect, apply a reviewed correction, and validate a remote redeployment.
- Use traces and source-access evidence to distinguish implementation faults from permission or protocol issues.
- Compare a controlled optimization against measurable accuracy, safety, and latency gates.
- Produce a release-readiness decision with explicit blockers and clean up assigned resources.

## Duration

**Estimated time:** 120 minutes

## Before you begin

Use the runtime from Exercise 03 or the provider's D3 checkpoint. The provider must keep the repair fixture isolated from core and supply the seeded incident and reset controls. Do not change a shared tenant policy to simulate a failure.

## Task 01: Repair and redeploy the qualification filter

### Introduction

Jordan must distinguish a broken sourcing filter from a working safety control. In the isolated fixture, the filter admits suppliers with expired or missing qualification expiry, but the independent guardrail correctly blocks their release.

### Description

In this task, you'll reproduce the defect, review a Copilot-assisted correction, extend boundary coverage, and prove that the repaired remote fixture ran. **Estimated time:** 40 minutes.

### Success criteria

- The original regression failures and blocked shortlist are reproduced without changing evidence or policy.
- The repaired filter rejects missing, malformed, and expired dates and accepts expiry exactly on launch.
- A new deployed fixture revision proposes only CMO-01, passes POL-01, and leaves core behavior unchanged.

### Learning resource

- [Starter qualification module](../../../../Labfiles/04-caldova-agents/Python/qualification-tool/qualification.py)
- [Independent policy](../../../../Labfiles/04-caldova-agents/Python/qualification-tool/policy.py)
- [Original runtime/export contract](../../../../Labfiles/04-caldova-agents/README.md)

### Key tasks

#### Key task 01: Reproduce the defect in isolation

Use the frozen fixture dates, not the core launch date or today's date.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open a new PowerShell terminal at the repository root and prepare the local tool environment. These tools need only the standard library, so no dependency installation is required.

    ```powershell
    Set-Location .\Labfiles\04-caldova-agents\Python\qualification-tool
    python -m venv .venv
    ```

1. Run the baseline and regression tests with the explicit interpreter path. This avoids changing organizational script-execution policy for virtual-environment activation.

    ```powershell
    .\.venv\Scripts\python.exe -m unittest discover -s tests -p test_baseline.py -v
    .\.venv\Scripts\python.exe -m unittest discover -s tests -p test_regression.py -v
    ```

1. Verify nine passing baseline tests and exactly two regression failures: expired qualification and missing expiry. Record actual output. If results differ, inspect your revision and whether the provider restored a repaired file instead of the defective checkpoint.
1. Generate the proposal and independent verdict. The guardrail's exit code 1 is expected for the defective shortlist.

    ```powershell
    .\.venv\Scripts\python.exe capacity_tool.py --case external-support --output results\before-proposal.json
    .\.venv\Scripts\python.exe gxp_checks.py --proposal results\before-proposal.json --output results\before-guardrail.json
    ```

1. Verify shortlist order CMO-02, CMO-03, CMO-01 and `passed=false`. Compare `qualification.py` with `policy.py`: the filter checks Approved status but omits expiry through November 30, 2026.
1. Invoke the same case against the isolated remote fixture endpoint and retain its rejected draft, loaded tool version, and POL-01 verdict. Don't change the main core endpoint to reproduce it.

    **Expected result:** You have both a code-level reproducer and a correlated remote failure. The guardrail rejection is correct behavior, not the defect to remove.

</details>

#### Key task 02: Apply a reviewed corrective action

Reuse the independently tested policy helper rather than creating a second date parser.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Add the qualification module, independent policy, and tests to GitHub Copilot Chat context. Request a correction limited to the qualification filter and new tests. Require preservation of the function signature, `required_through`, and explicit rejection reasons. Do not allow changes to source records, independent policy, guardrail, or answer keys.
1. Review the proposed diff. A valid repair reuses the existing strict policy helper without changing its implementation. Compare the proposal with this complete replacement for the starter module, which preserves its public signature and rejection reasons. Verify it doesn't compare against today's date or make an expired supplier valid because it is cheap.

    ```python
    from datetime import date
    from policy import qualification_issue as check_qualification

    def qualification_issue(cmo: dict, required_through: date) -> str | None:
        return check_qualification(cmo, required_through)
    ```

    This wrapper invokes the already-tested date validation rather than maintaining a second parser. The independent guardrail continues to evaluate source evidence itself.
1. Add a new test file `tests\test_expiry_boundaries.py` that exercises the repaired public function. The following complete test checks the launch-day boundary and invalid formats without changing the source fixture.

    ```python
    import unittest
    from datetime import date
    from qualification import qualification_issue

    class ExpiryBoundaryTests(unittest.TestCase):
        def test_expiry_boundaries(self):
            for expiry, valid in [
                ("2026-11-30", True), ("2026-11-29", False),
                ("2026-10-31", False), ("2027-01-01", True),
                (None, False), ("", False), ("not-a-date", False),
                ("20261130", False), ("2026-02-30", False),
            ]:
                with self.subTest(expiry=expiry):
                    record = {"qualification_status": "Approved",
                              "qualification_expiry": expiry}
                    issue = qualification_issue(record, date(2026, 11, 30))
                    self.assertEqual(issue is None, valid)

    if __name__ == "__main__":
        unittest.main()
    ```

1. Save the reviewed filter and tests with **Ctrl+S**. Run all tests and regenerate the same proposal and guardrail output.

    ```powershell
    .\.venv\Scripts\python.exe -m unittest discover -s tests -v
    .\.venv\Scripts\python.exe capacity_tool.py --case external-support --output results\after-proposal.json
    .\.venv\Scripts\python.exe gxp_checks.py --proposal results\after-proposal.json --output results\after-guardrail.json
    ```

1. Verify the 19 existing tests plus your new boundary test pass, only CMO-01 remains, and the guardrail returns exit code 0. If you add more tests, record the actual count rather than assuming 20.
1. Capture the failure, root cause, reviewed diff, test results, and residual risk in your incident log. Preserve independence of the release control.

    **Expected result:** The repair fixes the cause and covers both sides of the date boundary without weakening policy.

</details>

#### Key task 03: Redeploy and verify the remote correction

A local pass doesn't prove that the hosted tool imported the repaired module.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Use the provider's fixture deployment command to package the repaired qualification module and its policy dependency. Record the prior revision and exact source package path before deployment.
1. Deploy a new isolated fixture function/container revision. Record its version or image digest and verify that the fixture adapter targets it. Preserve the rollback command.
1. Repeat the original remote `external-support` request with the frozen October 1 decision date. Confirm 4,500 internal units, a 2,500-unit gap, only CMO-01, and a tool-derived POL-01 pass before final output.
1. Inspect the trace for the new tool version, not just the new agent prompt revision. If behavior is unchanged, check packaging, import caches, image digest, and the endpoint's selected revision.
1. Run the main core LP001 request again. Verify the gap remains 18,900 and supplier order remains CMO001, CMO002, CMO006 under core policy. No fixture IDs may appear in this answer.
1. Preserve before/after traces, deployment records, and regression results. Record restored or unexecuted work separately.

    **Expected result:** You can prove that the remote repair ran and that it did not contaminate the operational data profile.

</details>

Congratulations! You've diagnosed an implementation defect, applied a bounded correction, and validated its deployed effect while preserving Caldova's independent guardrail.

## Task 02: Diagnose integration and governance failures

### Introduction

A failed decision can originate in protocol configuration, stale code, permissions, or invalid evidence. Jordan must identify the failing boundary before making a corrective change.

### Description

In this task, you'll resolve one provider-seeded integration incident, verify agent ownership and source-access evidence, and test a harmless governance block. **Estimated time:** 30 minutes.

### Success criteria

- One integration incident has a reproducible symptom, evidence-backed cause, bounded corrective action, and successful retest.
- Six logical agents have real ownership and runtime-identity mappings.
- The isolated unapproved scraper is blocked, its invocation is denied, and permitted core decisions still work.

### Learning resource

- [Agent registry](/microsoft-365/admin/manage/agent-registry)
- [Connected Foundry agent prerequisites](/microsoft-copilot-studio/add-agent-foundry-agent)

### Key tasks

#### Key task 01: Isolate and correct an integration incident

Ask the provider to enable exactly one safe incident on your isolated revision. Don't randomly break a shared integration.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Reproduce the assigned failure with the original request. Record UTC time, channel, correlation/run ID, selected profile, source version, and deployed tool revision before making changes.
1. Follow the trace to the first failed boundary. Use this table to select a targeted diagnostic, not a speculative configuration reset.

    | Symptom | Evidence to inspect | Corrective action |
    | --- | --- | --- |
    | HTTP 400 mentions Activity | Connected agent ID and programmatic protocol configuration | Apply the provider-tested Activity enablement and retest the same connection |
    | Version-not-found HTTP 404 | Project generation, agent/version ID, published entry point | Restore the correct new-Foundry published ID, not a similarly named prompt agent |
    | Source access denied | Actual connection identity, source permission, audit event | Restore only the documented source grant for that identity; never broaden tenant access |
    | Old shortlist after repair | Image digest, packaged module, selected function revision | Deploy or select the reviewed artifact and confirm the next tool span uses it |
    | Duplicate event breaches | Replay scope, EventIDs, ingestion retries | Restrict to one cohort and deduplicate; don't raise the threshold to hide duplicates |
    | Guardrail timeout | Tool span/error and bounded retry policy | Restore the tool or approved timeout; preserve Needs review until a valid verdict exists |

1. State a root-cause hypothesis in the incident log and attach the trace/source evidence that supports it. Distinguish a failed connection from a denied policy decision.
1. Apply only the provider-authorized fix or restore the known-good configuration. Record what changed and which rollback restores it. Don't rotate unrelated credentials or disable the guardrail.
1. Repeat the original request and one adjacent negative test. Verify the intended behavior and the absence of an access or profile-isolation regression.

    **Expected result:** The corrective action resolves the evidenced cause rather than masking the symptom.

</details>

#### Key task 02: Verify ownership and actual runtime identity

Registry IDs, application IDs, Foundry IDs, and runtime Entra identities are different identifiers.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open the assigned administration surface in the [Microsoft 365 admin center](https://admin.microsoft.com). Locate **Agents** > **All agents** > **Registry**, or the provider's currently supported equivalent.
1. Locate Procurement Desk, Capacity Decision Orchestrator, Current Capacity, CMO Analysis, COO Recommendation, and Compliance Guardrail through the supported integration map. Don't assume internal helpers automatically become registry entries.
1. Record each logical name, accountable owner/sponsor, publisher, registry record ID, Foundry ID/version, and actual runtime identity. Resolve missing mappings with the provider rather than copying display names into identity fields.
1. Correlate one real decision with tool identities and source-access records. Verify that the observed identities match the approved connection map and have no unexpected write grants.
1. Export the provider-normalized `registry.json` for fixture evaluation. Preserve the six exact logical names from the original pack and unique runtime identity mappings. Don't hide genuinely distinct identities while removing duplicate lifecycle rows.

    **Expected result:** Ownership and observed execution are traceable without treating inventory metadata as a data-access log.

</details>

#### Key task 03: Block the isolated unapproved agent

Use only the provider's harmless training object and retain an actual denial test.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Locate `Unapproved CMO Scraper`. Verify its training-only identity, owner, lack of live crawling, and isolation from every other learner's workflow.
1. Apply **Block** using your scoped administrator identity. Wait for the provider's documented propagation interval and verify the recorded state.
1. Run the provider's harmless invocation test. Retain the denial response and identity evidence. A registry label alone isn't a complete denial test.
1. Run an authorized LP001 core decision and repeat the training-group access test. Confirm the authorized workflow still operates and the blocked identity never appears in its actual invoked IDs.
1. Compare actual data-processing/storage locations with Caldova's UK requirement. Record cross-geo, preview-support, expiry evidence, electronic-record controls, retention, and human approval as unresolved release items where appropriate.

    **Expected result:** The unwanted agent is denied without disrupting the permitted workflow or overstating regulatory compliance.

</details>

Congratulations! You've diagnosed an integration boundary and verified governance through execution evidence, not just agent descriptions or inventory labels.

## Task 03: Optimize and evaluate without regression

### Introduction

Jordan needs evidence that a change improves the system without removing safety controls. You measure a bounded optimization and keep core acceptance separate from the fixture's deterministic scorecard.

### Description

In this task, you'll establish a small repeatable baseline, apply one reversible optimization, evaluate actual runs, and decide whether to retain it. **Estimated time:** 30 minutes.

### Success criteria

- Before/after measurements use the same prompts, profile, source snapshot, model, and safety controls.
- A retained optimization reduces duplicate retrieval calls by at least 20%, doesn't increase median end-to-end latency, and introduces zero acceptance/safety failures.
- Core acceptance and all 24 fixture checks are recorded separately, with supported built-in metrics and missing metrics explicitly identified.

### Learning resource

- [Evaluate Foundry agents](/azure/foundry/observability/how-to/evaluate-agent)
- [Fixture cases](../../../../Labfiles/04-caldova-agents/data/evaluation-cases.jsonl) and [export requirements](../../../../Labfiles/04-caldova-agents/README.md)

### Key tasks

#### Key task 01: Establish a controlled baseline

Use a small engineering sample, not a claim of production throughput or a contractual service-level objective.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Freeze the deployed core revision, source snapshot, model/version, tool definitions, selected event replay, and generation settings supported by the runtime. Record them in the comparison manifest.
1. Define three prompts: the normal LP001 request; a request to explain the CMO006 simulated/core lead-time conflict; and a request to infer qualification from directory membership. Write expected quantities, uncertainty, and refusal/action boundaries before running them.
1. Run each prompt three times, with a fresh conversation per run. Exclude one separately recorded warm-up request from each revision. Record the nine real run IDs, UTC timing, end-to-end elapsed time, retrieval/tool counts, and token counts when available.
1. Inspect traces for repeated identical read-only policy or ontology retrievals within the same request. Select one duplication to eliminate using request-scoped reuse keyed by profile, source version, query, and effective authorization scope. If no duplication exists, retain the baseline and record that this optimization isn't justified.
1. Set acceptance gates before editing: at least 20% fewer total retrieval calls across the same nine-run cohort, median elapsed time no higher than baseline, all expected core results unchanged, and zero gate-order/access/profile-isolation failures.

    **Expected result:** You have a reproducible baseline and a measurable hypothesis. A performance change that fails the gates must be rolled back, not described as a win.

</details>

#### Key task 02: Apply and measure one reversible change

Don't optimize by removing the guardrail or hiding errors.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Use GitHub Copilot to propose eliminating only the evidenced duplicate retrieval using existing runtime helpers. Require request-scoped lifetime, exact authorization/source/profile keys, and no caching of tool errors or guardrail verdicts.
1. Review the diff and add the provider package's regression tests for changed source versions, changed identities, failed retrievals, and separate profiles. Reject cross-request/global caching and any new path that skips validation.
1. Run the provider's exact test command and deploy the candidate to your isolated revision. Record its digest and known-good rollback target.
1. Repeat the same nine requests under the recorded settings and selected replay. Re-run failed-verdict and restricted-source negative tests separately from the latency sample.
1. Calculate `100 * (baseline_calls - candidate_calls) / baseline_calls` for the cohort and compare median elapsed times. If baseline calls are zero, mark call reduction not applicable and reject this optimization hypothesis rather than dividing by zero.
1. Compare every correctness and safety result. Retain the change only if all declared gates pass. Otherwise restore the known-good revision with the provider command and verify one core request plus a negative test. Record unavailable token counts as **Not measured**.

    **Expected result:** The decision to retain or roll back is supported by recorded measurements and unchanged safety behavior, not a subjective faster response.

</details>

#### Key task 03: Evaluate the isolated repair fixture

The fixture evaluator requires exactly one real exported result for each supplied case. Performance repetitions belong in a different file.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open `data\evaluation-cases.jsonl` under the qualification pack. Use the three `query` values through the isolated repaired runtime, without putting the `expected` answer keys into model context.
1. Run `external-support`, `internal-sufficient`, and `conflicting-evidence` once each against the repaired revision. Use the provider exporter to write exactly three real records to `results\agent-results.jsonl` in the qualification-tool directory.
1. Verify the export matches the original runtime contract: typed quantities or explicit null, eligible IDs, facts/assumptions/gaps, next action, evidence-backed claims, tool-derived guardrail, and trace-derived identities/order/run ID. Add the real normalized registry export as `results\registry.json`.
1. Open a terminal at `Labfiles\04-caldova-agents\Python\qualification-tool` and run the evaluator with the environment created in the repair task. This command checks eight criteria per case, not model behavior or authenticity by itself.

    ```powershell
    .\.venv\Scripts\python.exe evaluate.py --results results\agent-results.jsonl --registry results\registry.json --output results\scorecard.json
    ```

1. Verify all 24 checks pass. Standard fixture: 4,500 internal, 2,500 remaining, CMO-01 only. Internal-sufficient: 7,500 internal, zero remaining, no CMO, guardrail still runs. Conflict: null quantities, no CMO, **Needs review**, failed guardrail and explicit resolution request.
1. Inspect the actual citations and source/audit traces yourself. A fabricated export could satisfy structural checks and is not acceptable evidence. Keep core result exports and repeated performance runs out of this three-case file.

    **Expected result:** The deterministic fixture scorecard has 24 genuine passes backed by real runtime evidence; an expected conflict rejection passes its safety expectation.

</details>

#### Key task 04: Review core quality and supported model evaluations

The core operational result has its own acceptance matrix. Neither its policy nor its missing evidence is identical to POL-01.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Check the deployed core result against every [workshop acceptance criterion](../index.md), using notebook/query evidence for quantities and traces for execution. Verify the full ordered shortlist, explicit uncertainty, selected replay references, and gate-before-final behavior.
1. In the provider-supported Foundry evaluation surface, configure the approved rubric and supported built-in evaluators for the actual target. Where available, include Task Adherence, Tool Call Accuracy, and Groundedness. Use actual messages, tool calls, and retrieved context with the current field mappings, not the answer-key JSONL alone.
1. Record evaluator versions, actual score scales, per-case pass thresholds, judge deployment, and dataset before starting. Require every tested case to meet the declared thresholds and manually verify critical claims. Don't assume every evaluator uses the same numeric scale.
1. Retain run IDs and per-case results. Mark missing metrics **Not evaluated**, timed-out jobs **Pending**, and unsupported targets **Blocked**. An incomplete required metric prevents a full readiness pass even if the local 24-check rubric passes.
1. Save your optimization comparison, rollback decision, core acceptance matrix, fixture scorecard, and model-evaluation evidence. Don't claim production performance from nine runs or regulatory compliance from an evaluator score.

    **Expected result:** You can distinguish measured improvement, deterministic correctness, model-quality evidence, and unresolved release requirements.

</details>

Congratulations! You've evaluated both data profiles and made an evidence-based optimization decision without weakening Caldova's controls.

## Task 04: Record readiness and clean up

### Introduction

Peter needs to understand both the provisional recommendation and the evidence that still prevents a production release. Jordan must leave the training estate in a known state without deleting shared resources.

### Description

In this task, you'll complete the release-readiness record, explain the customer outcome, and remove or restore assigned resources. **Estimated time:** 20 minutes.

### Success criteria

- A reviewer can trace customer requirements to implementation, incidents, corrective actions, versions, and validation evidence.
- The release decision states unresolved technical, data, regional, and regulatory requirements explicitly.
- Assigned billable/test resources and temporary credentials are removed or restored, with evidence retained according to policy.

### Key tasks

#### Key task 01: Make the readiness decision

A completed workshop and an approved customer production release are different conclusions.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Open your requirements matrix and link each row to actual evidence. Use **Passed**, **Failed**, **Blocked**, or **Not run** and identify an owner for every unresolved row.
1. Complete the following release gates. Don't use a failed or missing gate as an opportunity to weaken its threshold.

    | Gate | Required acceptance evidence |
    | --- | --- |
    | Core correctness | Exact LP001 baseline and provisional supplier order, eight delayed batches, and selected simulation cohort |
    | Runtime safety | Independent profile-specific verdict before every final output, with safe failed/missing/timeout/version-mismatch behavior |
    | Deployment | Actual reviewed revision, runtime identity, authenticated smoke test, source version, and usable rollback |
    | Access and actions | Verified procurement source boundary, training-group restriction, denied scraper, and idempotent follow-up receipt |
    | Repair and evaluation | Passing local repair/boundary tests, actual remote repair, separate 24-check fixture result, and required supported evaluator results |
    | Optimization | Recorded before/after cohort and thresholds, all safety gates retained, or verified rollback when improvement isn't established |
    | Customer readiness | Accountable quality/approval owners, expiry/transfer evidence, actual regional/data-flow approval, retention/audit design, and supported service/preview decision |

1. Record **Not approved for customer production release** if any required production evidence is unresolved. Name the specific blocker and owner rather than asserting that Agent 365 or a passed guardrail establishes GxP, GMP Annex 11, or 21 CFR Part 11 compliance.
1. Verify that the evidence pack identifies which activities you implemented, which checkpoint work was restored, and which activities were blocked or only observed.
1. Ask another learner or the instructor to locate one material claim's source record, one incident's corrective deployment, and the known-good rollback target from your evidence pack without using credentials.

    **Expected result:** The release decision is auditable and doesn't confuse training acceptance with validated regulated production operation.

</details>

#### Key task 02: Explain the business outcome and remaining work

Demonstrate the two workshop outcomes through concrete artifacts, not an unmeasured return-on-investment claim.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Write a short implementation summary for Peter: the core profile identifies an 18,900-unit gap and prioritizes provisional external options while retaining evidence and routing approval to the right humans.
1. Summarize one incident using symptom, cause, corrective change, deployed version, and successful retest. State separately whether the optimization met its declared threshold or was rolled back.
1. Explain the role boundary for each product: Copilot Studio for business interaction/actions, Foundry for agent runtime/tracing/evaluation, GitHub Copilot for reviewed development and the separate SDK harness, Fabric IQ for operational meaning, Foundry IQ for approved policy, and Agent 365 for administration.
1. Identify what remains before production, including actual source freshness, complete qualification/transfer evidence, region/data-flow approval, human authority, retention, monitoring, operational ownership, and service supportability.
1. Save the final summary with links to both the implemented/deployed solution evidence and the troubleshoot/optimize/validate evidence. Don't claim measured time savings or ROI without a customer baseline.

    **Expected result:** Your summary shows both requested learning outcomes and clearly states the remaining customer responsibilities.

</details>

#### Key task 03: Remove or restore only your assigned resources

Preserve approved evidence first. Shared resources and administrator-required blocks must remain intact.

<details markdown="block">
<summary><strong>Expand this section to view the solution</strong></summary>

1. Copy required evidence to the approved retention store and confirm you can open it. Exclude secrets and restrict sensitive trace/source exports.
1. Unpublish/remove your Teams installation and isolated Procurement Desk using the provider procedure. Remove your test follow-up items only after the retention check. Don't delete the shared supplier directory or qualification evidence.
1. Stop/delete your hosted runtime and fixture revisions, model deployments you exclusively own, and isolated connections using the provider's tested cleanup command. Verify no billable running revision remains assigned to you.
1. Stop the Eventstream source or revoke/rotate its training credential as directed. Clear the current terminal's simulation credential variables with these commands, which do not display their values.

    ```powershell
    Remove-Item Env:\EVENTSTREAM_CONNECTION_STRING -ErrorAction SilentlyContinue
    Remove-Item Env:\EVENTSTREAM_ENTITY_NAME -ErrorAction SilentlyContinue
    ```

1. Delete your dedicated Fabric workspace/items and dedicated Azure resource group only if the provider confirms exclusive ownership. For shared groups, have the provider remove only your named resources. Don't reset shared capacities or unblock the scraper contrary to administrator policy.
1. Remove temporary grants and local result exports after the retention check. If you activated any Python environment, run `deactivate`; the explicit interpreter paths in these tasks don't require activation. Sign out of lab accounts and retain the reviewed code changes according to the provider's submission process.
1. Verify the final resource inventory against the starting handout and record cleanup or restoration results and any provider-owned pending item.

    **Expected result:** Evidence remains available to authorized reviewers, while training-only resources and credentials don't remain active unintentionally.

</details>

Congratulations! You've implemented and deployed an evidence-backed agent solution, diagnosed and corrected implementation issues, and assessed its technical readiness without overstating production approval.

## Summary

You have successfully completed this exercise when the applicable task evidence is present and unresolved activities are labeled. You practiced core-data grounding, simulation-aware decisions, bounded actions, gated deployment, fault isolation, remote repair validation, controlled optimization, and accountable release assessment.
