"""Generate a Swagger/OpenAPI v2 definition supported by Copilot Studio connectors."""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.contracts import Settings, FollowUpRequest

def connector_document(cfg, origin):
    url = urlsplit(origin)
    if url.scheme != 'https' or not url.hostname or url.query or url.fragment or url.username or url.path not in ('','/'):
        raise ValueError('Use the actual HTTPS action API origin')
    scopes = {f'api://{cfg.api_audience}/Procurement.Read':'Read procurement lists',
              f'api://{cfg.api_audience}/FollowUp.Write':'Record a confirmed follow-up'}
    followup = FollowUpRequest.model_json_schema()
    confirmation = followup['properties']['confirmed']
    confirmation['enum'] = [confirmation.pop('const')]
    followup['description'] = 'A confirmed request. Verify human confirmation in the Studio conversation trace; retain the same UUID on retry.'
    operations = {}
    for path, operation in (('/rfps','GetRfps'),('/suppliers','GetSuppliers')):
        operations[path] = {'get':{'operationId':operation, 'summary':operation,
            'security':[{'Entra':[f'api://{cfg.api_audience}/Procurement.Read']}],
            'responses':{'200':{'description':'Approved procurement list records',
                'schema':{'type':'array','items':{'type':'object','properties':{
                    'item_id':{'type':'string'},'web_url':{'type':'string'},'fields':{'type':'object'}}}}}}}}
    operations['/follow-ups'] = {'post':{'operationId':'RecordFollowUp',
        'summary':'Record an explicitly confirmed RFP follow-up',
        'security':[{'Entra':[f'api://{cfg.api_audience}/FollowUp.Write']}],
        'parameters':[{'name':'body','in':'body','required':True,'schema':{'$ref':'#/definitions/FollowUpRequest'}}],
        'responses':{'200':{'description':'Actual persisted SharePoint receipt and audit reference',
            'schema':{'type':'object','properties':{
                'receipt_id':{'type':'string'},'list_id':{'type':'string'},
                'client_request_id':{'type':'string'},'rfp_id':{'type':'string'},
                'status':{'type':'string'},'duplicate':{'type':'boolean'},
                'award_approved':{'type':'boolean'},'audit':{'type':'object'}}}},
            '403':{'description':'Caller or permission denied'},
            '409':{'description':'Invalid RFP, schema or reused idempotency key'},
            '503':{'description':'Outcome unknown; retry only with the same UUID'}}}}
    return {'swagger':'2.0','info':{'title':'Caldova Procurement Actions','version':'1.0.0'},
        'host':url.netloc,'basePath':'/','schemes':['https'],'consumes':['application/json'],'produces':['application/json'],
        'paths':operations,'definitions':{'FollowUpRequest':followup},
        'securityDefinitions':{'Entra':{'type':'oauth2','flow':'accessCode',
            'authorizationUrl':f'https://login.microsoftonline.com/{cfg.tenant_id}/oauth2/v2.0/authorize',
            'tokenUrl':f'https://login.microsoftonline.com/{cfg.tenant_id}/oauth2/v2.0/token','scopes':scopes}}}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cfg = Settings.model_validate_json(args.config.read_text(encoding='utf-8-sig'))
    cfg.check_service()
    document = connector_document(cfg,args.url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__':
    main()
