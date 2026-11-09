"""Entra validation for the action API; no tokens or claims supplied in JSON."""
from __future__ import annotations
import asyncio
import jwt


class AccessDenied(Exception):
    pass


def authorize_claims(claims, cfg, permission):
    client = claims.get('azp') or claims.get('appid')
    if claims.get('tid') != cfg.tenant_id or client not in cfg.allowed_client_ids:
        raise AccessDenied('Tenant/client denied')
    oid = claims.get('oid')
    if oid not in cfg.allowed_user_oids:
        raise AccessDenied('Caller denied')
    grants = set(claims.get('scp', '').split()) | set(claims.get('roles', []))
    if permission not in grants:
        raise AccessDenied('Permission denied')
    return oid


class EntraAuth:
    def __init__(self, cfg):
        self.cfg = cfg
        self.issuer = f'https://login.microsoftonline.com/{cfg.tenant_id}/v2.0'
        self.jwks = jwt.PyJWKClient(f'https://login.microsoftonline.com/{cfg.tenant_id}/discovery/v2.0/keys', timeout=10)

    async def caller(self, authorization, permission):
        if not authorization or not authorization.startswith('Bearer '):
            raise AccessDenied('Bearer token required')
        token = authorization[7:]
        def verify():
            key = self.jwks.get_signing_key_from_jwt(token)
            return jwt.decode(token, key.key, algorithms=['RS256'], audience=self.cfg.api_audience,
                              issuer=self.issuer, options={'require':['exp','iat','nbf','tid','oid','aud','iss']})
        try:
            claims = await asyncio.to_thread(verify)
        except Exception as error:
            raise AccessDenied('Token validation failed') from error
        return authorize_claims(claims, self.cfg, permission)


def hosted_caller(context, cfg):
    """Only valid behind Foundry's private container ingress, never a public header API."""
    platform = context.platform_context
    subject = platform.original_subject
    if (not platform.call_id or subject is None or subject.tid != cfg.tenant_id
            or subject.oid not in cfg.allowed_user_oids):
        raise AccessDenied('Missing or unapproved platform caller context')
    return subject.oid, {'x-agent-foundry-call-id': platform.call_id}


def activity_caller(activity, platform, cfg):
    oid = getattr(activity.from_property, 'aad_object_id', None)
    tenant = (activity.channel_data or {}).get('tenant', {}).get('id')
    if (tenant != cfg.tenant_id or oid not in cfg.allowed_user_oids or platform is None
            or not platform.call_id or platform.original_subject is None
            or platform.original_subject.oid != oid or platform.original_subject.tid != tenant):
        raise AccessDenied('Channel user does not match authenticated platform caller')
    return oid, platform.platform_headers()
