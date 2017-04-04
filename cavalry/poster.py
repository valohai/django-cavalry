import json
import platform
from datetime import datetime
from logging import getLogger

import requests
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_bytes

from cavalry.stack import Stack

try:
    from ipware import get_ip
except ImportError:
    def get_ip(request): return request.META.get('REMOTE_ADDR')

log = getLogger(__name__)

sess = requests.Session()  # Persistent requests session, yes


class PayloadJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Stack):
            if not getattr(settings, 'CAVALRY_POST_STACKS', True):
                return ''
            return '\n'.join(obj.as_lines())
        return super().default(obj)


def post_stats(request, response, data):
    es_url_template = getattr(settings, 'CAVALRY_ELASTICSEARCH_URL_TEMPLATE', None)
    if not es_url_template:
        return
    payload = build_payload(data, request, response)
    es_url = es_url_template.format_map(
        dict(
            payload,
            ymd=datetime.utcnow().strftime('%Y-%m-%d'),
        ),
    )
    body = force_bytes(json.dumps(payload, cls=PayloadJSONEncoder))
    try:
        resp = sess.post(es_url, data=body, headers={'Content-Type': 'application/json'}, timeout=0.5)
        if resp.status_code != 201:
            log.warning('Unable to post data to %s (error %s): %s', es_url, resp.status_code, resp.text)
    except Exception as e:
        log.warning('Unable to post data to %s: %s', es_url, e)


def build_payload(data, request, response):
    payload = {
        'node': platform.node(),
        'content-type': response.get('content-type'),
        'ip': get_ip(request),
        'method': request.method,
        'params': dict(request.GET),
        'path': request.path,
        'status': response.status_code,
        'time': datetime.utcnow(),
    }
    resolver_match = getattr(request, 'resolver_match', None)
    if resolver_match:
        payload.update({
            'view': resolver_match.view_name,
        })
    user = getattr(request, 'user', None)
    if user:
        payload.update({
            'user_id': user.id,
        })
    payload.update(data)
    payload.pop('start_time', None)
    payload.pop('end_time', None)
    payload.pop('db_record_stacks', None)
    return payload
