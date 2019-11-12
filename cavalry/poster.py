import json
import platform
from datetime import datetime
from logging import getLogger

import requests
from django.core.handlers.wsgi import WSGIRequest
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.utils.encoding import force_bytes
from requests import Response

from cavalry.policy import can_serialize_stacks, get_request_es_url_template
from cavalry.stack import Stack

try:
    from ipware import get_ip
except ImportError:

    def get_ip(request: WSGIRequest) -> str:
        return request.META.get('REMOTE_ADDR')


log = getLogger(__name__)

sess = requests.Session()  # Persistent requests session, yes


class PayloadJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Stack):
            if not can_serialize_stacks(request=None):
                return ''
            return '\n'.join(obj.as_lines())
        return super().default(obj)


def post_stats(request: WSGIRequest, response: HttpResponse, data: dict) -> Response:
    es_url_template = get_request_es_url_template(request)
    if not es_url_template:
        return None
    payload = build_payload(data, request, response)
    es_url = es_url_template.format_map(
        dict(payload, ymd=datetime.utcnow().strftime('%Y-%m-%d')),
    )
    body = force_bytes(json.dumps(payload, cls=PayloadJSONEncoder))
    try:
        resp = sess.post(
            es_url, data=body, headers={'Content-Type': 'application/json'}, timeout=0.5
        )
        if resp.status_code != 201:
            log.warning(
                'Unable to post data to %s (error %s): %s',
                es_url,
                resp.status_code,
                resp.text,
            )
        return resp
    except Exception as e:
        log.warning('Unable to post data to %s: %s', es_url, e)


def build_payload(data: dict, request: WSGIRequest, response: HttpResponse) -> dict:
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
        payload.update(
            {'view': resolver_match.view_name,}
        )
    user = getattr(request, 'user', None)
    if user:
        payload.update(
            {'user_id': user.id,}
        )
    payload.update(data)
    payload.pop('start_time', None)
    payload.pop('end_time', None)
    payload.pop('db_record_stacks', None)
    return payload
