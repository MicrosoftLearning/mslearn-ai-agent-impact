// Caldova L400 Ex2: provisions group site + 3 procurement lists + seed data.
// Run in the browser console of https://<tenant>.sharepoint.com (signed in as an admin), step 1,
// then on https://<tenant>.sharepoint.com/sites/CaldovaLaunchTeam, steps 2-3.
// Verified in the dev tenant on 6 Nov 2026. A PnP PowerShell equivalent would make this a one-command setup.

// STEP 1 (root site): create the M365 group + team site "Caldova Launch Team"
async function step1(){
  const d=await fetch('/_api/contextinfo',{method:'POST',headers:{Accept:'application/json;odata=nometadata'}}).then(r=>r.json());
  const r=await fetch('/_api/GroupSiteManager/CreateGroupEx',{method:'POST',headers:{Accept:'application/json;odata=nometadata','Content-Type':'application/json;odata=nometadata','X-RequestDigest':d.FormDigestValue},
    body:JSON.stringify({displayName:'Caldova Launch Team',alias:'CaldovaLaunchTeam',isPublic:false,optionalParams:{Description:'Caldova L400 lab: procurement lists and Procurement Desk audience',CreationOptions:['SPSiteLanguage:1033']}})});
  return r.json();
}

// STEP 2 (group site): lists and columns
const W='/sites/CaldovaLaunchTeam';
async function hdr(){const d=await fetch(W+'/_api/contextinfo',{method:'POST',headers:{Accept:'application/json;odata=nometadata'}}).then(r=>r.json());return {Accept:'application/json;odata=nometadata','Content-Type':'application/json;odata=verbose','X-RequestDigest':d.FormDigestValue};}
async function step2(){
  const h=await hdr();
  const post=(u,b,x={})=>fetch(W+u,{method:'POST',headers:{...h,...x},body:JSON.stringify(b)});
  const list=(t,desc)=>post('/_api/web/lists',{__metadata:{type:'SP.List'},BaseTemplate:100,Title:t,Description:desc});
  const field=(l,xml)=>post(`/_api/web/lists/getbytitle('${l}')/fields/createfieldasxml`,{parameters:{__metadata:{type:'SP.XmlSchemaFieldCreationInformation'},SchemaXml:xml,Options:8}});
  const title=(l,disp,u)=>post(`/_api/web/lists/getbytitle('${l}')/fields/getbyinternalnameortitle('Title')`,{__metadata:{type:'SP.Field'},Title:disp,Indexed:u,EnforceUniqueValues:u},{'X-HTTP-Method':'MERGE','IF-MATCH':'*'});
  await list('Supplier Directory','SUP-01 Caldova procurement supplier directory (synthetic). Being listed here is NOT qualification approval.');
  await title('Supplier Directory','Supplier ID',true);
  for (const x of ['<Field Type="Text" Name="SupplierName" StaticName="SupplierName" DisplayName="Supplier"/>','<Field Type="Text" Name="Service" StaticName="Service" DisplayName="Service"/>','<Field Type="Text" Name="ProcurementContact" StaticName="ProcurementContact" DisplayName="Procurement contact"/>','<Field Type="Text" Name="DirectoryStatus" StaticName="DirectoryStatus" DisplayName="Directory status"/>']) await field('Supplier Directory',x);
  await list('RFP Tracker','Procurement RFP tracker (synthetic). Procurement IDs (CMO-01) are separate from core supplier IDs (CMO001).');
  await title('RFP Tracker','RFP ID',true);
  for (const x of ['<Field Type="Text" Name="SupplierId" StaticName="SupplierId" DisplayName="Supplier ID"/>','<Field Type="Text" Name="Service" StaticName="Service" DisplayName="Service"/>','<Field Type="Choice" Name="Status" StaticName="Status" DisplayName="Status"><CHOICES><CHOICE>Open</CHOICE><CHOICE>Closed</CHOICE></CHOICES></Field>','<Field Type="DateTime" Format="DateOnly" Name="LastUpdated" StaticName="LastUpdated" DisplayName="Last updated"/>','<Field Type="Boolean" Name="FollowUpRequested" StaticName="FollowUpRequested" DisplayName="Follow-up requested"><Default>0</Default></Field>']) await field('RFP Tracker',x);
  await list('FollowUpRequests','Append-only RFP follow-up requests. One item per unique ClientRequestId. The item ID is the receipt.');
  await title('FollowUpRequests','RFP ID',false);
  for (const x of ['<Field Type="Text" Name="ClientRequestId" StaticName="ClientRequestId" DisplayName="ClientRequestId" Required="TRUE" Indexed="TRUE" EnforceUniqueValues="TRUE"/>','<Field Type="Note" Name="RequestText" StaticName="RequestText" DisplayName="RequestText" RichText="FALSE" NumLines="6"/>','<Field Type="Text" Name="CallerOid" StaticName="CallerOid" DisplayName="CallerOid" Required="TRUE"/>','<Field Type="Text" Name="PayloadHash" StaticName="PayloadHash" DisplayName="PayloadHash" Required="TRUE"/>','<Field Type="Boolean" Name="Confirmed" StaticName="Confirmed" DisplayName="Confirmed"><Default>0</Default></Field>']) await field('FollowUpRequests',x);
}

// STEP 3 (group site): seed data
async function step3(){
  const d=await fetch(W+'/_api/contextinfo',{method:'POST',headers:{Accept:'application/json;odata=nometadata'}}).then(r=>r.json());
  const h={Accept:'application/json;odata=nometadata','Content-Type':'application/json;odata=nometadata','X-RequestDigest':d.FormDigestValue};
  const add=(l,o)=>fetch(W+`/_api/web/lists/getbytitle('${l}')/items`,{method:'POST',headers:h,body:JSON.stringify(o)});
  for (const [id,n,c] of [['CMO-01','Caldova Partner A','partner-a@example.invalid'],['CMO-02','Caldova Partner B','partner-b@example.invalid'],['CMO-03','Caldova Partner C','partner-c@example.invalid']]) await add('Supplier Directory',{Title:id,SupplierName:n,Service:'Sterile fill-finish',ProcurementContact:c,DirectoryStatus:'Listed for sourcing'});
  for (const [id,s,st,dt] of [['RFP-01','CMO-01','Open','2026-10-01'],['RFP-02','CMO-02','Open','2026-10-01'],['RFP-03','CMO-03','Closed','2026-09-28']]) await add('RFP Tracker',{Title:id,SupplierId:s,Service:'Sterile fill-finish',Status:st,LastUpdated:dt+'T12:00:00Z',FollowUpRequested:false});
}

// STEP 4 (group site): show the new columns in each list's default view (createfieldasxml doesn't add them)
async function step4(){
  const d=await fetch(W+'/_api/contextinfo',{method:'POST',headers:{Accept:'application/json;odata=nometadata'}}).then(r=>r.json());
  const h={Accept:'application/json;odata=nometadata','X-RequestDigest':d.FormDigestValue};
  const m={'Supplier Directory':['SupplierName','Service','ProcurementContact','DirectoryStatus'],'RFP Tracker':['SupplierId','Service','Status','LastUpdated','FollowUpRequested'],'FollowUpRequests':['ID','ClientRequestId','RequestText','CallerOid','PayloadHash','Confirmed','Author','Created']};
  for (const [l,fs] of Object.entries(m)) for (const f of fs) await fetch(W+`/_api/web/lists/getbytitle('${l}')/defaultview/viewfields/addviewfield('${f}')`,{method:'POST',headers:h});
}
