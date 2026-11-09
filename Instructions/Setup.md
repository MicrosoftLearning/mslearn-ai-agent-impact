# Tenant and workstation setup

## Current release gate

This repository supplies the Caldova workshop source, supporting assets and configuration examples.
Do not start a task whose required live component is missing, and do not count an
offline result as a deployed workflow.

The lab uses the learner's authorized tenant and subscriptions. Permissions and
entitlements are prerequisites for each engineer's tenant.
Interactive authentication is acceptable. No tenant changes or deployments are made
by the repository's offline tests.

## Get the correct revision

```powershell
git clone https://github.com/MicrosoftLearning/mslearn-ai-agent-impact.git
Set-Location mslearn-ai-agent-impact
git rev-parse HEAD
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe scripts/validate_repository.py
```

Use the assigned working branch and capture its commit ID. After the change is merged, clone the MicrosoftLearning repository's `main` branch instead.

The included asset manifests and required files must exist in the selected checkout.
If they are absent, resolve the checkout/version mismatch; no private import workflow is needed.

## Supplied files and boundaries

| Area | Location | What is supplied |
|---|---|---|
| Core context | `Allfiles/L300-TW-Data` | Six CSVs, curation notebook, event publisher, KQL, business-context instructions and supporting policy documents |
| Repair fixture | `Labfiles/04-caldova-agents` | Frozen scenario/policy, procurement seed, instructions, qualification tools, solution reference, tests and evaluator |
| L400 specifications | `Labfiles/04-caldova-agents/l400-*.md` | Core agent contract and BYOS runtime/readiness requirements |
| Full runtime | `runtime/`, `deploy/`, `scripts/runtime_admin.py` | Hosted orchestration/SDK guardrail, isolated fixture, authenticated action API, actual service adapters, deployment, export and recovery |
| Local core tools | `runtime/core.py` | Source-derived assessment and independent deterministic proposal validation |
| Repository checks | `scripts/validate_repository.py` | Offline package/contract checks only |

Preserve the intentionally defective qualification filter. Exercise 4 is where the
learner repairs it. The inherited notebook date-normalization problem is also retained
because Exercise 1 explicitly teaches its diagnosis/correction. The syntax check does
not claim that PySpark ran or that those date conversions succeeded.

The original L300 integration README is retained as background for the fixture. The
L400 instructions, core contract and this setup guide take precedence.

## Local environment record

Copy `config/lab.example.json` to `config/lab.local.json` and record only actual values.
The local file is ignored by Git. Empty fields mean **not configured**, not a default.
Never add passwords, bearer tokens, connection strings, or secret values to either file.
Use the real signed-in user's delegated connection where required; an application
identity is not a substitute merely because it has broad permissions.

The record is the overall environment inventory. The four service configuration examples
are consumed by the executable runtime. Follow [Runtime setup](Runtime.md) for their
actual fields, identity initialization, source pin, deployment and validation order.

## Tenant readiness (complete before the lab starts)

The tenant admin completes this checklist at least **1 hour** before learners start.
Fabric tenant settings can take up to an hour to apply. Learners don't change tenant
settings themselves.

| Setting or item | Where | Required value | Used by |
|---|---|---|---|
| Users can create Fabric items | Fabric Admin portal > Tenant settings | Enabled | All Fabric items |
| **Users can create Ontology (preview) items** | Fabric Admin portal > Tenant settings | **Enabled** (disabled by default) | Ex1 Task 3 |
| Users can use Copilot, AI Agents and other AI experiences powered by Azure OpenAI | Fabric Admin portal > Tenant settings | Enabled | Ontology query, Fabric data agent |
| Capacities can be designated as Fabric Copilot capacities | Fabric Admin portal > Tenant settings | Enabled | Data agent on the capacity |
| Allow non-Entra ID auth in Eventstream | Fabric Admin portal > Tenant settings | Enabled | Ex1 Task 2 replay |
| Capacity region | Azure portal | A US or EU Data Boundary region | Data agent without cross-geo processing |
| Capacity SKU | Azure portal | Paid F-SKU (F2 is enough for Ex1). Fabric trial may be unavailable | Ex1 |

For capacities outside the supported processing geography, the tenant administrator
must review the cross-geography AI processing/storage requirements and approve the
settings before use. Select an approved supported region if consent is not available.

**Learner self-check (first step of Ex1 Task 3):** in the workspace select **+ New item**
and search **Ontology**. If **Ontology (preview)** is missing, or **Create** fails with
"not currently supported in this workspace", tell the coach. After the setting is
enabled, creation can keep failing for about 15 to 20 minutes.

## Capacity and workspace setup

Follow [Prepare the isolated Fabric foundation](Fabric-Foundation.md) to create or
assign the capacity and workspace. This is prerequisite setup, outside the timed
exercises. Reuse recorded resources on resume. The live foundation test used F2;
it does not establish a size or region for every runtime/channel workload.

## Exercise 2 preparation

Use [the supplied SharePoint/flow assets](../lifecycle/ex2/README.md) to prepare the
procurement lists, RecordFollowUp connection and audience group. Learners still perform
their Copilot Studio knowledge and tool configuration hands-on.

## Build and validate the supplied runtime

Follow [Build and operate the L400 runtime](Runtime.md). The repository supplies the
implementation, three infrastructure templates, immutable image build, source adapters,
SDK harness, action definition generator and evidence/recovery commands. Actual models,
quota, delegated connections, consent, selected-list grants, Studio publishing and channel
access must be configured and verified in the assigned tenant. The six-hour estimate
excludes prerequisite provisioning and does not yet include a measured full-runtime pilot.

Use the [readiness contract](../Labfiles/04-caldova-agents/l400-provider-readiness.md)
as the acceptance specification. D0-D4 use actual captured runtime checkpoints plus external service exports, **not
preexisting cloud snapshots**. The word provider in retained instructions means the assigned
administrator or setup owner, not a preprovisioned Skillable lab.

## Preserve the learner work

Do not precomplete Lakehouse curation, event replay, ontology binding, Procurement Desk
configuration, orchestration repair, remote deployment validation, the qualification
repair, measured optimization, or the final readiness decision. Recovery assets may
restore a failed stage, but restored work must be labeled as such.

## What a local pass means

A local pass establishes package consistency and deterministic code behavior. It does
not prove cloud access boundaries, available quota, preview integration compatibility,
model quality, runtime identity, source audit evidence, or end-to-end execution.

After performing the Exercise 4 repair, the focused fixture tests should pass. The
package checker can be run with `--fixture-state repaired` to permit the edited
qualification module; it is still not a live acceptance test.
