---
title: TechWorkshop - Deliver real business impact with Caldova agents
permalink: index.html
layout: home
---

# TechWorkshop: Deliver real business impact with Caldova agents

Caldova needs a defensible response to a 7% launch-capacity gap. Peter, the chief operating officer (COO), needs a recommendation backed by manufacturing evidence. Alex in procurement needs supplier and request-for-proposal (RFP) tracking without unrestricted manufacturing access. Jordan, the platform engineer, must implement, deploy, diagnose, and validate the agent runtime.

You act as Jordan, with an assigned procurement authoring identity and a scoped governance identity when required. You curate supplied data, replay operational events, build a procurement entry point, configure specialist agents, deploy the prepared runtime, repair implementation defects, and measure a controlled optimization. This is hands-on implementation, not an architecture discussion or product demonstration.

**Level:** 400. **Estimated working time:** 360 minutes (six hours), excluding breaks and provider provisioning. The time boxes are authoring estimates and require a pilot delivery.

## Outcomes

After you complete the workshop, you'll be able to:

- Implement and deploy an agentic solution that satisfies the defined customer-scenario requirements.
- Troubleshoot and optimize an agentic solution by identifying the causes of implementation issues, applying corrective actions, and validating that the solution meets the defined technical and production-readiness criteria.

## Architecture

The solution follows this interaction path:

```text
Teams -> Caldova Procurement Desk (Copilot Studio)
      -> Capacity Decision Orchestrator (Microsoft Foundry)
         -> Current Capacity -> CMO Analysis when a gap remains
         -> COO Recommendation draft -> Compliance Guardrail
         -> approved decision-support summary or Needs review
```

Fabric IQ supplies governed operational context from curated core data and the ontology. The event simulator supplies explicitly synthetic signals through an Eventstream and Eventhouse. Foundry IQ supplies approved policy context. SharePoint supplies procurement knowledge and an append-only follow-up action. These sources aren't interchangeable.

The Foundry team has five logical agents: one orchestrator and four specialists. Together with Procurement Desk, there are six. The guardrail uses a provider-supplied GitHub Copilot SDK harness and a deterministic tool. Separately, GitHub Copilot in VS Code assists with code changes. Agent 365 supplies inventory and administration, not workflow execution.

## Prerequisites

To complete this workshop, you need:

- Experience with Python, source control, Azure identities, basic Fabric queries, and agent tools. You don't need to design the architecture during the exercise.
- An isolated, provider-approved Fabric workspace and capacity, Lakehouse and Eventhouse creation rights, Eventstream authoring, and access to the supported Fabric IQ ontology integration.
- A prepared Microsoft Foundry project, model deployment, policy knowledge base, runtime source package, tool adapters, deployment permissions, and tested deployment and rollback commands.
- A training Microsoft 365 tenant with Copilot Studio authoring, SharePoint procurement access, the prepared follow-up flow, Teams publication rights, and scoped Agent 365 administration.
- VS Code, GitHub Copilot, Git, Azure CLI, and Python 3.13 or later. The local qualification pack was previously checked with Python 3.14.5; use the provider's separately pinned hosted SDK interpreter and dependencies. Don't assume every dependency supports the newest Python release.
- A working copy of the `L400-unify-data` branch from your lab provider and the [L400 provider handout requirements](../../../Labfiles/04-caldova-agents/l400-provider-readiness.md).

> **Important:** This repository does not contain the deployable orchestrator, hosted SDK container, authenticated core-policy adapter, cloud export adapter, or tenant checkpoints. The provider must supply and smoke-test those assets before delivery. If they are missing, stop the affected implementation task. A local run or labeled walkthrough does not satisfy the deployment outcome.

> **Note:** Fabric IQ, hosted-agent integrations, the Foundry connection in Copilot Studio, and some evaluation surfaces are preview or actively developed features. Verify availability and supported versions before delivery. Passing this training exercise is not a production certification.

## Keep the two data profiles separate

The customer case study describes a UK-residency requirement. The supplied core dataset includes plants outside the UK and uses a different launch date and capacity model from the original lab fixture. Treat these differences as explicit constraints, not errors to silently overwrite.

| Property | Main operational solution: `core` | Isolated repair harness: `qualification-fixture` |
| --- | --- | --- |
| Source | Six CSVs in `Allfiles/L300-TW-Data/data/core` | `Labfiles/04-caldova-agents/data/scenario.json` |
| Launch | LP001, product P101, November 26, 2026 | November 30, 2026; decision clock October 1, 2026 |
| Capacity model | Target 270,000; qualified 251,100; authoritative gap 18,900 | Required additional 7,000; internal 4,500; remaining 2,500 |
| Plant and supplier IDs | PL001 through PL003; CMO001, CMO002, CMO006 | CAP-01 through CAP-03; CMO-01 through CMO-06 |
| Supplier decision | Core eligibility rules and score order; provisional human review | Strict qualification expiry through launch under POL-01 |
| Event clock | Replay-time UTC, explicitly simulated | Frozen fixture dates; no event replay |

Never map `CMO001` to `CMO-01` or apply the fixture's 24-check evaluator to a core decision. The core files have no certification-expiry field or complete transfer approval evidence. A current-status label does not establish qualification through launch. Keep final procurement approval and actual launch readiness pending quality review.

## Acceptance criteria

| Requirement | Evidence required before you mark it complete |
| --- | --- |
| Correct core decision | LP001 gap 18,900; binding plant PL003; eight delayed batches; eligible order CMO001, CMO002, CMO006 under the documented core rules |
| Correct streaming interpretation | One replay has 10 unique events and four strict threshold breaches; no modification to the authoritative launch gap |
| Scoped business interaction | Procurement citations, a real follow-up receipt, idempotent retry, denied restricted-source access, and training-group-only activation |
| Executable agent runtime | Real specialist calls, authenticated tools, versioned deployments, and a tool-derived guardrail verdict before every final answer |
| Corrective action | Reproduced qualification bug, reviewed repair, boundary tests, deployed revision, and a trace proving the new remote implementation ran |
| Measured optimization | Same test cohort before and after, recorded latency/calls/tokens where available, no safety or accuracy regression, and a rollback decision |
| Production-readiness decision | Core acceptance matrix, separate 24-check fixture scorecard, evaluator results, identity/access evidence, and explicit unresolved release blockers |

## Record evidence safely

Create an evidence folder in the provider-approved store, not in Git. Keep a requirements matrix, source manifest, deployment/version inventory, incident log, evaluation exports, performance comparison, and release decision. Record real run IDs, UTC timestamps, and actual identity mappings. Never copy credentials, connection strings, raw restricted records, or invented trace metadata into the evidence pack.

A requirement is **Passed** only with the requested evidence. Use **Failed**, **Blocked**, or **Not run** otherwise. An expected safe rejection can pass a safety test, but it doesn't turn an incorrect implementation into a successful deployment. Preserve the original [110-minute exercise](../04-caldova-governed-agents.md) as a separate exercise.

## Exercises
<hr>

{% assign labs = site.pages | where_exp:"page", "page.url contains '/Instructions/Labs'" %}
{% for activity in labs  %}
{% if activity.lab.title %}
### [{{ activity.lab.title }}]({{ site.github.url }}{{ activity.url }})


{% if activity.lab.level %}**Level**: {{activity.lab.level}} \| {% endif %}{% if activity.lab.duration %}**Duration**: {{activity.lab.duration}}{% endif %}

{% if activity.lab.description %}
*{{activity.lab.description}}*
{% endif %}
<hr>
{% endif %}
{% endfor %}
