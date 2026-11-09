"""Build the CaldovaFollowUp unmanaged solution (RecordFollowUp agent flow).

Lab asset: imported during the Ex2 setup (pac solution import) so learners
never hand-build the idempotency plumbing. They attach the flow as a tool,
map the inputs and test confirm / retry / reject behaviour.

Usage: python3 build_recordfollowup_solution.py --site <site-url> --rfp-list <guid> --fur-list <guid> --out <zip>
"""
import argparse, json, zipfile, uuid

WORKFLOW_ID = "8c3f1b2a-6d1e-4f0a-9b7c-2c5a4e7d9f10"
CONN_REF = "cal_sharepoint_caldova"
SP_API = "/providers/Microsoft.PowerApps/apis/shared_sharepointonline"

# Input keys are named explicitly. The designer's default keys (text, text_1...) surface in
# Copilot Studio as Input.text / Input.text_1 and confuse both makers and the orchestrator.
T = "triggerBody()?['rfp_id']"
T1 = "triggerBody()?['request_text']"
T2 = "triggerBody()?['client_request_id']"
T3 = "triggerBody()?['caller_oid']"   # mapped to System.User.Id in the tool, never AI-filled


def sp(op, params, run_after):
    return {
        "type": "OpenApiConnection",
        "inputs": {
            "host": {"connectionName": "shared_sharepointonline", "operationId": op, "apiId": SP_API},
            "parameters": params,
            "authentication": "@parameters('$authentication')",
        },
        "runAfter": run_after,
    }


def respond(status, receipt, message, run_after=None):
    props = {k: {"title": k, "type": "string", "x-ms-content-hint": "TEXT", "x-ms-dynamically-added": True}
             for k in ("status", "receipt_id", "message")}
    return {
        "type": "Response", "kind": "Skills",
        "inputs": {"schema": {"type": "object", "properties": props},
                   "statusCode": 200,
                   "body": {"status": status, "receipt_id": receipt, "message": message}},
        "runAfter": run_after or {},
    }


def text_input(desc, title):
    return {"description": desc, "title": title, "type": "string",
            "x-ms-content-hint": "TEXT", "x-ms-dynamically-added": True}


def matched_receipt(lookup, suffix, run_after=None):
    """Return a prior receipt only when the persisted request matches exactly.

    The legacy PayloadHash field contains truncated base64, not a cryptographic
    hash. Compare the stored fields, including the caller, instead of trusting it.
    The outer count check prevents first() on an empty/ambiguous result.
    """
    row = f"first(body('{lookup}')?['value'])"
    return {
        "type": "If",
        "expression": {"and": [
            {"equals": [f"@length(body('{lookup}')?['value'])", 1]},
        ]},
        "actions": {f"Check_exact_request_{suffix}": {
            "type": "If",
            "expression": {"and": [
                {"equals": [f"@{row}?['ClientRequestId']", f"@{T2}"]},
                {"equals": [f"@{row}?['Title']", f"@{T}"]},
                {"equals": [f"@{row}?['RequestText']", f"@{T1}"]},
                {"equals": [f"@{row}?['CallerOid']", f"@{T3}"]},
                {"equals": [f"@{row}?['Confirmed']", True]},
                {"not": {"equals": [f"@empty(string({row}?['ID']))", True]}},
            ]},
            "actions": {f"Respond_duplicate_{suffix}": respond(
                "duplicate", f"@{{string({row}?['ID'])}}",
                "An identical confirmed request is recorded. Returning its verified receipt.")},
            "else": {"actions": {f"Respond_conflict_{suffix}": respond(
                "rejected", "",
                "This client request ID is already in use for a different request. No receipt is returned. Do not report success.")}},
            "runAfter": {},
        }},
        "else": {"actions": {f"Respond_unverified_{suffix}": respond(
            "failed", "",
            "The write outcome could not be verified. No receipt is available. Do not report success; retry only the identical confirmed request with the same client request ID.")}},
        "runAfter": run_after or {},
    }


def definition(site, rfp_list, fur_list):
    quote = chr(39)
    esc = lambda e: f"replace({e},{quote * 4},{quote * 6})"
    lookup = {"dataset": site, "table": fur_list,
              "$filter": f"ClientRequestId eq '@{{{esc(T2)}}}'", "$top": 2}
    new_request = {
        "Get_open_RFP": sp("GetItems", {
            "dataset": site, "table": rfp_list,
            "$filter": f"Title eq '@{{{esc(T)}}}' and Status eq 'Open'", "$top": 2}, {}),
        "Check_RFP_is_open": {
            "type": "If",
            "expression": {"and": [{"equals": ["@length(body('Get_open_RFP')?['value'])", 1]}]},
            "actions": {
                "Create_follow_up": sp("PostItem", {
                    "dataset": site, "table": fur_list,
                    "item/Title": f"@{{{T}}}",
                    "item/ClientRequestId": f"@{{{T2}}}",
                    "item/RequestText": f"@{{{T1}}}",
                    "item/CallerOid": f"@{{{T3}}}",
                    # Retained for list compatibility; NOT used to establish a match.
                    "item/PayloadHash": f"@{{take(base64(concat({T},'|',{T1})),255)}}",
                    "item/Confirmed": True}, {}),
                "Check_created_receipt": {
                    "type": "If",
                    "expression": {"and": [{"not": {"equals": ["@empty(string(body('Create_follow_up')?['ID']))", True]}}]},
                    "actions": {"Respond_created": respond(
                        "created", "@{string(body('Create_follow_up')?['ID'])}", "Follow-up request recorded.")},
                    "else": {"actions": {"Respond_missing_receipt": respond(
                        "failed", "", "A write was attempted but no receipt was returned. Do not report success; retry the identical request with the same client request ID.")}},
                    "runAfter": {"Create_follow_up": ["Succeeded"]},
                },
                # A timeout or any failed write may have persisted. Read once; only
                # an actual identical row establishes recovery. Never retry POST here.
                "Get_after_failure": sp("GetItems", lookup,
                    {"Create_follow_up": ["Failed", "TimedOut"]}),
                "Check_recovered_request": matched_receipt(
                    "Get_after_failure", "recovery", {"Get_after_failure": ["Succeeded"]}),
                "Respond_recovery_failed": respond(
                    "failed", "", "The write outcome could not be checked. Do not report success; retry only the identical confirmed request with the same client request ID.",
                    {"Get_after_failure": ["Failed", "TimedOut"]}),
            },
            "else": {"actions": {"Respond_rejected": respond(
                "rejected", "", "The RFP was not found uniquely or is not Open. No follow-up was created.")}},
            "runAfter": {"Get_open_RFP": ["Succeeded"]},
        },
        "Respond_RFP_lookup_failed": respond(
            "failed", "", "The RFP could not be checked. No write was attempted. Retry the same request ID after resolving access or availability.",
            {"Get_open_RFP": ["Failed", "TimedOut"]}),
    }
    # Disable automatic create retries: a unique key protects the list, and the
    # explicit read-back path recovers the real receipt without an extra POST.
    new_request['Check_RFP_is_open']['actions']['Create_follow_up']['inputs']['retryPolicy'] = {'type': 'none'}
    return {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {"$connections": {"defaultValue": {}, "type": "Object"},
                       "$authentication": {"defaultValue": {}, "type": "SecureObject"}},
        "triggers": {"manual": {
            "type": "Request", "kind": "Skills",
            "inputs": {"schema": {"type": "object", "properties": {
                "rfp_id": text_input("Open RFP ID from the RFP Tracker, for example RFP-01", "rfp_id"),
                "request_text": text_input("Follow-up request text the requester confirmed", "request_text"),
                "client_request_id": text_input("Unique client request ID, reused unchanged on retries", "client_request_id"),
                "caller_oid": text_input("Entra object ID of the signed-in user (map to System.User.Id)", "caller_oid"),
            }, "required": ["rfp_id", "request_text", "client_request_id", "caller_oid"]}},
        }},
        "actions": {
            # Exact retries remain recoverable even if the RFP was closed since
            # the original successful write. New requests still require Open.
            "Get_existing_request": sp("GetItems", lookup, {}),
            "Check_duplicate": {
                "type": "If",
                "expression": {"and": [{"equals": ["@empty(body('Get_existing_request')?['value'])", False]}]},
                "actions": {"Check_existing_request": matched_receipt("Get_existing_request", "existing")},
                "else": {"actions": new_request},
                "runAfter": {"Get_existing_request": ["Succeeded"]},
            },
            "Respond_initial_lookup_failed": respond(
                "failed", "", "Existing requests could not be checked. No write was attempted. Retry the same request ID after resolving access or availability.",
                {"Get_existing_request": ["Failed", "TimedOut"]}),
        },
    }

def build(site, rfp_list, fur_list, out):
    wf = {"properties": {
        "connectionReferences": {"shared_sharepointonline": {
            "runtimeSource": "embedded",
            "connection": {"connectionReferenceLogicalName": CONN_REF},
            "api": {"name": "shared_sharepointonline"}}},
        "definition": definition(site, rfp_list, fur_list),
        "templateName": ""},
        "schemaVersion": "1.0.0.0"}
    wf_file = f"Workflows/RecordFollowUp-{WORKFLOW_ID.upper()}.json"

    solution = f"""<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml version="9.2.25101.185" SolutionPackageVersion="9.2" languagecode="1033" generatedBy="CrmLive" OrganizationVersion="9.2.25101.185" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.25101.00185" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <SolutionManifest>
    <UniqueName>CaldovaFollowUp</UniqueName>
    <LocalizedNames><LocalizedName description="Caldova Follow-up (lab asset)" languagecode="1033" /></LocalizedNames>
    <Descriptions><Description description="RecordFollowUp agent flow, imported during the Ex2 setup." languagecode="1033" /></Descriptions>
    <Version>1.0.0.2</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>caldovalab</UniqueName>
      <LocalizedNames><LocalizedName description="Caldova Lab" languagecode="1033" /></LocalizedNames>
      <Descriptions />
      <EMailAddress xsi:nil="true"></EMailAddress>
      <SupportingWebsiteUrl xsi:nil="true"></SupportingWebsiteUrl>
      <CustomizationPrefix>cal</CustomizationPrefix>
      <CustomizationOptionValuePrefix>48210</CustomizationOptionValuePrefix>
      <Addresses />
    </Publisher>
    <RootComponents>
      <RootComponent type="29" id="{{{WORKFLOW_ID}}}" behavior="0" />
    </RootComponents>
    <MissingDependencies />
  </SolutionManifest>
</ImportExportXml>
"""
    customizations = f"""<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" OrganizationVersion="9.2.25101.185" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.25101.00185">
  <Entities />
  <Roles />
  <Workflows>
    <Workflow WorkflowId="{{{WORKFLOW_ID}}}" Name="RecordFollowUp" Description="Records a confirmed RFP follow-up idempotently and returns a receipt.">
      <JsonFileName>/{wf_file}</JsonFileName>
      <Type>1</Type>
      <Subprocess>0</Subprocess>
      <Category>5</Category>
      <Mode>0</Mode>
      <Scope>4</Scope>
      <OnDemand>0</OnDemand>
      <TriggerOnCreate>0</TriggerOnCreate>
      <TriggerOnDelete>0</TriggerOnDelete>
      <AsyncAutodelete>0</AsyncAutodelete>
      <SyncWorkflowLogOnFailure>0</SyncWorkflowLogOnFailure>
      <StateCode>1</StateCode>
      <StatusCode>2</StatusCode>
      <RunAs>1</RunAs>
      <IsTransacted>1</IsTransacted>
      <IntroducedVersion>1.0.0.0</IntroducedVersion>
      <IsCustomizable>1</IsCustomizable>
      <BusinessProcessType>0</BusinessProcessType>
      <IsCustomProcessingStepAllowedForOtherPublishers>1</IsCustomProcessingStepAllowedForOtherPublishers>
      <PrimaryEntity>none</PrimaryEntity>
      <LocalizedNames><LocalizedName languagecode="1033" description="RecordFollowUp" /></LocalizedNames>
    </Workflow>
  </Workflows>
  <FieldSecurityProfiles />
  <Templates />
  <EntityMaps />
  <EntityRelationships />
  <OrganizationSettings />
  <optionsets />
  <CustomControls />
  <EntityDataProviders />
  <connectionreferences>
    <connectionreference connectionreferencelogicalname="{CONN_REF}">
      <connectionreferencedisplayname>Caldova SharePoint</connectionreferencedisplayname>
      <connectorid>{SP_API}</connectorid>
      <iscustomizable>1</iscustomizable>
      <statecode>0</statecode>
      <statuscode>1</statuscode>
    </connectionreference>
  </connectionreferences>
  <Languages><Language>1033</Language></Languages>
</ImportExportXml>
"""
    content_types = ('<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="xml" ContentType="application/octet-stream" />'
                     '<Default Extension="json" ContentType="application/octet-stream" /></Types>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("solution.xml", solution)
        z.writestr("customizations.xml", customizations)
        z.writestr(wf_file, json.dumps(wf, indent=2))
    with open(out.replace(".zip", ".definition.json"), "w") as f:
        json.dump(wf, f, indent=2)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--site", required=True)
    p.add_argument("--rfp-list", required=True)
    p.add_argument("--fur-list", required=True)
    p.add_argument("--out", default="CaldovaFollowUp_1_0_0_2.zip")
    a = p.parse_args()
    build(a.site, a.rfp_list, a.fur_list, a.out)
    print("built", a.out)
