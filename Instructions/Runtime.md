# Build and operate the L400 runtime

Use the [setup guide](Setup.md) to prepare the tenant and runtime prerequisites.
The commands below apply to the learner's working copy.

This repository now supplies the executable runtime, container targets, deployment
templates, action API, tests and evidence/recovery commands for Exercises 2–4.
The implementation has offline contract coverage. A complete Azure/Fabric/Studio/Teams
pilot is still required. An active container, a local test, or a successful model response
does not establish that pilot passed.

Run commands from this repository's root on the learner workstation.
Use actual resource names and IDs. Keep learner modifications on a local working branch.

## Components and trusted boundaries

| Component | Source | Execution and permissions |
|---|---|---|
| Capacity Decision Orchestrator | `runtime/orchestrator.py`, `runtime/server.py` | Hosted Foundry Responses + Activity, fixed core LP001 profile; six ordered runtime spans; no manufacturing writes |
| Current Capacity / CMO Analysis | `scripts/runtime_admin.py` specialist definitions | Pinned Foundry prompt versions; supported delegated Fabric IQ connection; CMO also retrieves the approved policy index |
| COO Recommendation | Same specialist definitions | Structured findings only; no tools; strict draft contract |
| Compliance Guardrail | `runtime/guardrail.py` | Separate hosted identity; real Copilot SDK session invokes `ValidateCoreDecision`; independently reads the same pinned curated tables |
| Qualification exercise | `runtime/fixture.py` | Separate image, hosted name, identity and three specialist versions; original `AssessCandidates`, SDK `gxp-checks`, POL-01 and frozen scenarios |
| Procurement actions | `runtime/procurement.py` | Separate Container App and identity; Graph selected-list reads and confirmed append-only follow-ups; signed Entra tokens |
| Evidence | `runtime/adapters.py`, `runtime/trace.py` | Private Entra-authorized Blob storage; runtime UUIDs, ordered times/durations, actual Foundry response/version IDs and token usage when returned |

The live core adapter reads the six curated Fabric SQL tables. It never loads repository
CSVs as a fallback. The independent core validator retains the existing provisional
contract. Operational events are a separately verified ten-event cohort with four strict
breaches; they cannot replace the launch gap. Fabric IQ must execute for both operational
specialists; otherwise release fails. A SQL read alone does not pass the ontology gate.

The policy retrieval implementation uses the supported Foundry Azure AI Search tool
over an approved policy index. It does not claim that an unconfigured Foundry IQ knowledge
base exists. Record this concrete connection in the identity map and validate its actual
retrieved policy text. `AssessCoreCapacity` runs in trusted orchestration code, rather
than exposing an arbitrary SQL/path tool to the model.

Core, guardrail and action services never load the qualification fixture. Only the
`fixture` container target includes its four Python modules and frozen data. Setup
preserves the defective `qualification.py`; Exercise 4 repairs and redeploys it.

## 1. Install and validate the package

Use Python 3.12, Git and the Azure CLI. The build runs remotely in ACR, so local Docker
is optional. Install ODBC Driver 18 on the operator VM for the SQL pinning command.
The image installs that driver and predownloads the SDK's checksum-verified runtime.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/validate_repository.py
az login
az account show
```

The two qualification regression failures are **expected in the starter**. The package
checker checks exactly those failures. Do not replace the starter with its solution.
The core orchestrator is a reference implementation: Exercise 3 students inspect its
release checks, add a reviewed change, rerun failure tests and deploy their own revision.

## 2. Supply the Azure and Fabric foundation

Complete [Fabric foundation](Fabric-Foundation.md), then Exercise 1. Retain its six
curated tables, complete ontology metadata and actual completed replay ID. Do not prefill
learner answers or pretend that a priming cohort is the completed replay.

Use an existing approved Foundry project/model, or deploy `deploy/foundry.bicep` into the
isolated resource group. Supply `location`, `accountName`, `projectName`,
`modelDeploymentName`, `modelName`, `modelVersion`, `modelSkuName` and `modelCapacity`
from the approved regional catalog/quota. No model, geography or capacity is assumed.
Supply names and region to `deploy/foundation.bicep` for ACR and private evidence storage.

Create standard ARM parameter files under ignored `config/*.local.json`, then deploy:

```powershell
az deployment group create --resource-group $resourceGroup --template-file deploy/foundation.bicep --parameters @config/foundation.parameters.local.json
az deployment group create --resource-group $resourceGroup --template-file deploy/foundry.bicep --parameters @config/foundry.parameters.local.json
$revision = git rev-parse HEAD
.\scripts\Build-Runtime.ps1 -Registry $registryName -Revision $revision
```

The second deployment is optional if reusing the approved project. Record actual outputs.
The build requires a clean checkout and the exact full commit ID. After a reviewed
student code change, commit only that source change before assigning `$revision` again.
Keep local configuration, state and evidence ignored; never commit them to clear the check.
Read `state/images-<revision>.json`; use its immutable `@sha256:` images for deployment.
The Docker base and OS package repositories are resolved at build time; the recorded
result digest, rather than a mutable tag, is the rollback artifact.

In Foundry, create the supported **Fabric IQ ontology connection** using incoming Entra
user context or a separately established managed/custom OAuth session. Keep the exact
connection ID. Signing into Azure in a browser does not automatically establish every
service's delegated connection. Confirm a permitted caller can query the actual ontology
and a restricted identity cannot. A service principal token is not an ontology OAuth
substitute. Preserve actual entity/query traversal evidence; entity names in prose do
not prove a relationship query.

Create the approved core policy index in Azure AI Search using the business-context
instructions and core policy limitations. Use Entra/RBAC authentication, a project
connection and index-scoped read access for the applicable runtime identity. Record the
actual connection/index names. Do not index fixture policy as core policy. Confirm a
real retrieval of the missing-expiry/transfer limitations before accepting CMO output.

## 3. Establish identities and local configuration

Copy the four `config/*.example.json` service files to corresponding `*.local.json`
files. Fill actual tenant/project, revision, evidence account URL without a trailing
slash, evidence container, approved callers and endpoints. Empty fields are deliberately
invalid for serving; no sample identity is a successful configuration.

Use separate hosted names such as your assigned names for guardrail, orchestrator and
fixture. Initialize each name with the **core image**, then read its returned actual
`instance_identity.principal_id` and `client_id`:

```powershell
.\.venv\Scripts\python.exe scripts/runtime_admin.py initialize --config config/guardrail.local.json --name $guardrailName --image $coreImage --output state/guardrail-identity.json
```

Repeat with the orchestrator and fixture config/name. Initialization needs only
`tenant_id` and `project_endpoint` in the JSON. It creates an inert hosted version that
always returns `Not configured`, then pins that version. It does not query any source.
If identity creation is pending, rerun on the **same name**. Copy the real principal and
client IDs into the service configuration. The deploy command checks the principal ID
against Foundry; never use the project identity or a guessed GUID in its place.

Assign only the following grants, to those actual identities:

| Identity | Required grants |
|---|---|
| Core orchestrator | Foundry User on the specific project; SELECT on the six curated SQL tables; read/query on the assigned Eventhouse database; Blob create/read on its evidence container |
| Core guardrail | Independent SELECT on the same six tables, model inference rights on its approved Azure OpenAI deployment, evidence-container access; no Eventhouse/SharePoint/manufacturing writes |
| Fixture runtime | Its isolated Foundry project/versions, approved model inference and isolated evidence container; no production Fabric or SharePoint grants |
| Procurement action identity | Selected supplier/RFP lists read, selected follow-up list write, its evidence container and ACR pull; no manufacturing grants |
| Student/developer | Project authoring rights, approved delegated Fabric access, SQL pin/export access and resource deployment rights on the assigned resource group |
| Procurement-only test user | Approved procurement/channel access; no raw manufacturing/Fabric grant |

Fabric SQL grants are SQL/data-plane permissions; Azure Owner alone does not grant them.
Use the SQL endpoint's approved administration interface to grant the named principal
CONNECT/SELECT on exactly the six tables. Do not grant tenant-wide Fabric access. Give
the guardrail's model identity the documented inference role at the approved model/account
scope. Storage access uses Entra, with shared keys and anonymous blob access disabled.

For hosted services, `allowed_user_oids` contains the actual approved original callers
forwarded by Foundry. Production deployment uses the platform credential chain, without
the developer's CLI login. The container ingress must remain private behind Foundry;
its platform headers are not an authentication interface for a public self-hosted server.
An opaque call ID is forwarded only to first-party Foundry APIs. Missing original-subject
or delegated channel context fails closed; never replace it with a display name/header.

## 4. Pin the source and create specialists

Fill guardrail SQL host/database/schema and approved Azure OpenAI endpoint/deployment.
Use its actual core source pin for both core services:

```powershell
.\.venv\Scripts\python.exe scripts/runtime_admin.py source-pin --config config/guardrail.local.json --output config/guardrail.pinned.local.json
```

Review the output and replace your guardrail local configuration with the pinned copy.
Copy the `records-sha256:` value to the orchestrator configuration. This command actually
reads the curated SQL tables using your signed-in identity and checks the core contract.
Serving repeats the read under the service identity and rejects a changed hash. It does
not equate your successful read with the runtime identity's successful read.

Fill `config/core-specialists.local.json` from its example with actual model, connection,
index and accountable owner values. Create pinned specialists:

```powershell
.\.venv\Scripts\python.exe scripts/runtime_admin.py specialists --config config/guardrail.local.json --plan config/core-specialists.local.json --output state/core-specialists.json
```

Copy the returned name/version pairs to orchestrator `agents.capacity`, `agents.cmo`
and `agents.coo`. Configure an entirely separate fixture specialist plan and invoke the
same command to produce its three actual references. Do not reuse core versions there.

Deploy the guardrail first, using the core image, then check its actual status:

```powershell
.\.venv\Scripts\python.exe scripts/runtime_admin.py deploy --config config/guardrail.local.json --name $guardrailName --image $coreImage --output state/guardrail-deployment.json
.\.venv\Scripts\python.exe scripts/runtime_admin.py status --config config/guardrail.local.json --name $guardrailName --version $guardrailVersion --output state/guardrail-status.json
```

Take `$guardrailVersion` from the deployment record; status may require several minutes.
Do not create another version just to poll. Copy the actual name/version into the core
orchestrator's fourth reference. Fill its real Eventhouse query URI, database and eight
hexadecimal replay ID, then deploy the orchestrator using the same commands/config.
Deploy the fixture service with its **fixture image** and separate config/name.

## 5. Invoke, export, verify, then route

Invoke a concrete candidate version rather than `latest`:

```powershell
.\.venv\Scripts\python.exe scripts/runtime_admin.py invoke --config config/orchestrator.local.json --name $orchestratorName --version $candidateVersion --input config/requests/core.json --output evidence/core-invocation.json
.\.venv\Scripts\python.exe scripts/runtime_admin.py export --config config/orchestrator.local.json --input evidence/core-invocation.json --output evidence/core-record.json
.\.venv\Scripts\python.exe scripts/verify_live.py --config config/orchestrator.local.json --records evidence/core-record.json --output evidence/core-checked.jsonl
```

Export downloads the private blob and matches the hash returned by the runtime. The
checker requires cloud-mode runtime spans, exact pinned revision/identity/source, actual
Fabric calls, specialist IDs and the SDK callback. Inspect its retained raw tool output,
source access/audit records and citations too. `Ready for review` means a **provisional
core decision**, never an award or qualification approval through launch.

Verify the guardrail with tampered gap, supplier and source-version requests. In an
isolated orchestrator candidate, set `allow_test_faults=true` and `fault_mode` to
`timeout`, `missing-verdict` or `wrong-version`, deploy, invoke, and require **Needs review**.
These are labeled fault injections, not actual service outages. The missing/incorrect
verdict modes still execute the real guardrail before altering its test-bound result;
the timeout mode deliberately prevents that call. Request JSON cannot enable a hook.
Restore `fault_mode=none`, `allow_test_faults=false` for the accepted candidate.

After the positive/negative checks, select the actual candidate for the endpoint:

```powershell
.\.venv\Scripts\python.exe scripts/runtime_admin.py route --config config/orchestrator.local.json --name $orchestratorName --version $candidateVersion --activity --output state/core-route.json
```

This pins Responses and Activity to one version. Existing sessions keep their previous
version; start a new session/conversation when verifying routing or restoring a checkpoint.
The native Activity SDK validates channel authentication. If the live channel lacks the
required original user/delegated context, the runtime returns Needs review. Capture and
resolve the connection/OAuth configuration; do not bypass that check to make Teams pass.

## 6. Build the procurement action and connect Studio/Teams

### Supported Exercise 2 route: imported Copilot Studio flow

Prepare SharePoint and the RecordFollowUp solution using [the supplied setup assets](../lifecycle/ex2/README.md).
Bind the flow's actual connection and requester field, attach it as a tool in Copilot Studio,
require explicit user confirmation, and publish only to the approved security group.
Verify the actual list item and receipt. A repeat with the same caller, RFP, request
text and request ID must return the original receipt; conflicting reuse must reject.

The flow executes under its SharePoint connection account. Its `caller_oid` field
attributes the request but does not impersonate the user for SharePoint permissions.
Verify the effective connection permissions separately.

### Alternative API implementation (engineering reference)

The following Container App/API implementation is retained as optional reference code.
It uses a different UUID request-ID and authorization contract. Do not substitute it
for the supported flow without reviewing that distinction and validating the separate path.


In your isolated SharePoint site, create supplier directory and RFP lists using the
approved suppliers and `rfp-tracker.csv`. Keep procurement IDs `CMO-01` separate from core
`CMO001`. Use `Title=RFP-01` etc. for RFP keys, with **indexed unique Title**. The API
reads only Title, SupplierId, Status, Owner, Contact, DueDate and Description.

Create a separate follow-up list with these exact internal column names:

| Column | SharePoint type / rule |
|---|---|
| Title | Single line text; RFP ID |
| ClientRequestId | Single line text, required, indexed, **enforce unique values** |
| RequestText | Multiple lines, plain text |
| CallerOid | Single line text, required |
| PayloadHash | Single line text, required |
| Confirmed | Yes/No |

Use list settings to verify uniqueness, not only the displayed name. The API recovers
a concurrent duplicate by rereading this unique key; it never blindly retries POST.
A key reused by a different caller or payload is rejected. If a response is lost, retain
the same UUID for recovery. The receipt is the actual Graph item ID/link; it is not a
purchase order. There are no PATCH, DELETE, award or manufacturing routes.

An administrator registers the action API as **single tenant**, requests v2 access tokens,
exposes delegated `Procurement.Read` and `FollowUp.Write` scopes at `api://<API-client-id>`,
and grants the approved connector client consent. Put the API's **GUID client ID** in
`api_audience`, permitted OAuth client IDs in `allowed_client_ids`, and real approved
caller object IDs in `allowed_user_oids`. The API verifies signature, tenant issuer,
audience, expiry, client, caller and permission. Group membership must also be enforced
in Studio/channel publishing; a prompt is not a group boundary.

Create the action user-assigned identity before filling its real principal/client IDs:

```powershell
az identity create --resource-group $resourceGroup --name $actionIdentityName --location $location
```

Grant Graph `Lists.SelectedOperations.Selected` plus **read** assignments on the supplier
and RFP lists and **write** on the follow-up list (or your organization's approved
selected-site alternative with its broader scope explicitly recorded). Consent and
selected-list grants are administrator work; Azure Owner does not imply Graph consent.
Give this identity access to its separate evidence container. Set `managed_identity_client_id`
to its actual client ID and `runtime_identity_oid` to its actual principal ID.

Deploy `deploy/procurement.bicep` with region, environment/app/identity/registry names,
the immutable **core image**, and the complete local procurement config as `runtimeConfig`.
The template reuses that identity and assigns ACR pull. Its HTTP API requires the Entra
token described above. Generate the action definition for the actual returned HTTPS URL:

```powershell
.\.venv\Scripts\python.exe scripts/export_connector.py --config config/procurement.local.json --url $actionApiUrl --output state/procurement.openapi.json
```

The generator emits Swagger/OpenAPI **v2**, which the Power Platform connector import
supports; it does not hand Studio the development API's OpenAPI 3.1 document.
In Copilot Studio, import this definition as an OAuth-authenticated REST tool.
If the environment uses custom connectors, create an OAuth 2.0 Entra connector for the
same operations/scopes and bind it as the agent tool. Complete its real delegated
connection, configure end-user authentication, and test a denied token as well as a
permitted user. Importing a definition alone does not create that connection.

Attach supplier/RFP SharePoint knowledge to **Caldova Procurement Desk** with end-user
source authentication and citations. Configure `GetRfps`, `GetSuppliers` and
`RecordFollowUp`. For the latter, collect the exact RFP and request text, show them to
the user, obtain explicit confirmation, generate one UUID, and retain it across retries.
`confirmed=true` is a transport assertion: verify the Studio confirmation branch actually
ran in the conversation trace; the API cannot infer a human confirmation from that flag.

Under **Agents > Add an agent > Microsoft Foundry**, connect the **published orchestrator
agent ID**, not a specialist/version display name. Route only core capacity questions to
it, using the core instructions. Publish to the approved training group/Teams channel.
Start a new conversation and preserve one correlated procurement-only and one capacity
request. Verify no raw restricted records are returned and that the actual restricted
identity cannot read the source. Retain the real out-of-group activation denial.

Studio publishing, connection binding, consent and channel configuration remain hands-on UI tasks.
The flow solution generator is supplied in `lifecycle/ex2`; generating its ZIP is not a substitute for importing and testing it.

## 7. Qualification repair, evidence and recovery

Run the three fixture request files against its **starter** version and retain its failed
independent qualification verdict. Repair `qualification.py` in Exercise 4, rerun the
local checks with `--fixture-state repaired`, build a new fixture image/digest and deploy
that candidate. Do not edit the fixed independent `policy.py` to make the bug pass.

Invoke `external-support`, `internal-sufficient` and `conflicting-evidence` once each
using their files in `config/requests`. Export each private evidence record with the
same `export` command. Then create the original evaluator's JSONL from those actual runs:

```powershell
.\.venv\Scripts\python.exe scripts/verify_live.py --config config/fixture.local.json --records evidence/external-support-record.json evidence/internal-sufficient-record.json evidence/conflicting-evidence-record.json --output Labfiles/04-caldova-agents/Python/qualification-tool/results/agent-results.jsonl
```

Run the original evaluator with the **actual** normalized registry export as Exercise 4
describes. `inventory` in `runtime_admin.py` retrieves real Foundry version records for
an operator-supplied mapping; it refuses a missing owner/registry mapping or an unverified
Studio record. Obtain the Studio/Agent 365 record through its authenticated export and
merge using actual IDs, retaining the original source export. The helper does not invent
an Agent 365 enrollment for internal helpers. Missing supported mappings/denial tests
remain an explicit readiness gap.

Capture immutable runtime checkpoints after your real work:

```powershell
.\.venv\Scripts\python.exe scripts/runtime_admin.py checkpoint --stage D3 --config config/orchestrator.local.json --input state/core-deployment.json --output state/D3.json
.\.venv\Scripts\python.exe scripts/runtime_admin.py restore --config config/orchestrator.local.json --input state/D3.json --output state/restored-D3.json
```

| Checkpoint | Retain with the runtime/configuration record |
|---|---|
| D0 | Approved foundation IDs, licenses/consent, inert initialized identities and original repo revision |
| D1 | Curated-table pin, date checks, ontology metadata/version, completed replay ID and source/query evidence |
| D2 | SharePoint IDs/schema/seeds, authenticated action/knowledge connections, real Studio draft export |
| D3 | Accepted immutable core/guardrail/fixture versions, image digests, local configuration, route and positive/negative traces |
| D4 | Repaired fixture digest, three live exports/scorecard, measured optimization and final readiness decision |

The checkpoint command captures runtime state; D0–D2 external Fabric/Studio/SharePoint
artifacts must be exported through those services' real interfaces. They are not invented
cloud snapshots. Save each corresponding artifact beside the checkpoint. Restore does
not rewind SharePoint writes, fabricate notebook work or restore tenant policy. It
selects the retained immutable hosted version and returns its saved configuration.
Check that configuration against the unchanged source pin, restore the corresponding
external service artifact if needed, and rerun a new-session positive **and** negative
test. Keep previous images/versions available. A deleted version cannot be rolled back.

Optimization changes must be reversible and measured against the same source/replay and
case mix. Compare actual response usage when returned, otherwise record `Not measured`.
Do not count timing from transport doubles as service performance. Keep repeated runs
outside the evaluator's three-case file. Export evidence before removing only resources
and selected grants assigned to this lab; ending a shared lab is not a cleanup command.

## Service references

- [Foundry hosted runtime contract](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agent-contract)
- [Hosted version identity, routing and rollback](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/manage-hosted-agent)
- [Fabric IQ authentication and tool](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric-iq)
- [Foundry Azure AI Search tool](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/ai-search)
- [Copilot SDK Python](https://github.com/github/copilot-sdk/tree/main/python)
- [Graph list column uniqueness](https://learn.microsoft.com/en-us/graph/api/resources/columndefinition)
- [Connect a Foundry agent to Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/add-agent-foundry-agent)
- [Studio REST tool specification requirements](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agent-extend-action-rest-api)
