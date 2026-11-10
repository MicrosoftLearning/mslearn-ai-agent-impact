# Ex2 setup assets (procurement entry point)

Ex2 assumes a prepared SharePoint site, a RecordFollowUp flow and a Teams audience group.
None of them exist in a fresh tenant. These assets create them in a few minutes so class
time goes to the agent work: knowledge, tool, confirmation gate and access boundary.
The original setup and flow were tested in the developer tenant on 6 November 2026.

Participants bring their own Microsoft tenant, so the tenant admin runs these steps once
in each participant tenant before class (pre-work, about 10 minutes).

| Step | Asset | Creates | Time |
|---|---|---|---|
| 1 | `provision-caldova-sharepoint.js` | M365 group and site **Caldova Launch Team**; lists **Supplier Directory**, **RFP Tracker**, **FollowUpRequests** with unique keys, view fields and seed rows (CMO-01..03, RFP-01..03) | < 1 min |
| 2 | `build_recordfollowup_solution.py` | Solution zip **CaldovaFollowUp** with the **RecordFollowUp** agent flow and a SharePoint connection reference | < 1 min build, about 1 min import |
| 3 | Entra security group (see below) | **Caldova Procurement Users**, the only audience the agent is shared with | < 1 min |

## 1. SharePoint site, lists and seed data

Run in the browser console, signed in as the tenant admin: `step1()` on
`https://<tenant>.sharepoint.com`, then `step2()`, `step3()` and `step4()` on
`https://<tenant>.sharepoint.com/sites/CaldovaLaunchTeam`. Dates are written at 12:00 UTC
so date-only values don't show a day early on US-time sites.

A PnP PowerShell port is the next step for a one-command setup.

## 2. RecordFollowUp agent flow

```bash
python build_recordfollowup_solution.py \
  --site https://<tenant>.sharepoint.com/sites/CaldovaLaunchTeam \
  --rfp-list <RFP Tracker list GUID> --fur-list <FollowUpRequests list GUID> \
  --out CaldovaFollowUp_1_0_0_2.zip
pac solution import --path CaldovaFollowUp_1_0_0_2.zip
```

Flow behaviour: a new request requires an Open RFP. An identical retry returns
its original receipt, even when the original RFP has subsequently closed. Reusing
a client request ID for another caller, RFP or request text is rejected without
disclosing the previous receipt. The retained PayloadHash list field is not a
cryptographic hash and must not be treated as proof of identity.

Responses contain `status`, `receipt_id` and `message`. Valid statuses are
`created`, `duplicate`, `rejected` and `failed`. After a failed or timed-out
create, the flow reads back and returns `duplicate` only when it finds a
confirmed matching record with a real item ID. No row, mismatched data, ambiguous
results or failed read-back return `failed`, never a fabricated receipt.
Use the original client request ID when retrying an uncertain write.

In the lab, learners add the flow as a tool, map `caller_oid` to `System.User.Id` (custom
value, never filled by AI) and set **Ask the end user before running = Yes**.

## 3. Audience security group

The Teams share dialog only lists security-enabled groups. The M365 group from step 1 is
not security-enabled, so create a security group:

```powershell
$g = New-MgGroup -DisplayName 'Caldova Procurement Users' -MailEnabled:$false `
  -MailNickname 'caldova-procurement-users' -SecurityEnabled
New-MgGroupMember -GroupId $g.Id -DirectoryObjectId <learner user object ID>
```

Agent users also need the **Basic User** security role in the Power Platform
environment because the agent uses a Power Platform connector as a knowledge source.

## Setup and verification

Keep the existing JavaScript SharePoint setup. Import the unmanaged flow solution
into the intended Power Platform environment and bind its SharePoint connection
reference before attaching it to Copilot Studio. The flow uses the connection
owner's permissions; `System.User.Id` records the requester, not delegated
SharePoint access. Validate list scope and the approved Teams audience independently.

Exercise the confirmed create, unchanged retry, reused ID with changed text or
another authorized test caller, invalid RFP, and failed write/read-back paths;
compare every returned receipt with the actual FollowUpRequests list.
