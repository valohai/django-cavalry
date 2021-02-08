from threading import Thread

import django
from django.db import connections
from django.template.response import SimpleTemplateResponse

from cavalry.locals import managed
from cavalry.policy import (
    can_cavalrize,
    can_inject_stats,
    can_post_stats,
    can_post_threaded,
    can_record_stacks,
)
from cavalry.poster import post_stats
from cavalry.reporter import inject_stats
from cavalry.timing import get_time

if django.VERSION[0] == 2:
    from cavalry import db_django2 as db_module
else:
    from cavalry import db_django3 as db_module


def _process(request, get_response):
    with db_module.enable_db_tracing(), managed(
        db_record_stacks=can_record_stacks(request),
    ) as data:
        data['start_time'] = get_time()
        response = get_response(request)
        if isinstance(response, SimpleTemplateResponse):
            response.render()
        data['end_time'] = get_time()
        data['duration'] = data['end_time'] - data['start_time']
        data['databases'] = {}
        for conn in connections.all():
            queries = [q for q in conn.queries if "hrtime" in q]
            if queries:
                total_time = sum(q.get('hrtime', 0) * 1000 for q in queries)
            else:
                total_time = 0
            data['databases'][conn.alias] = {
                'queries': queries,
                'n_queries': len(queries),
                'time': total_time,
            }

    if can_inject_stats(request):
        inject_stats(request, response, data)

    if can_post_stats(request):
        post_stats_kwargs = {'request': request, 'response': response, 'data': data}
        if can_post_threaded(request):
            Thread(
                name='cavalry poster',
                target=post_stats,
                kwargs=post_stats_kwargs,
                daemon=False,
            ).start()
        else:
            post_stats(**post_stats_kwargs)

    return response


def cavalry(get_response):
    def middleware(request):
        if not can_cavalrize(request):
            return get_response(request)
        return _process(request, get_response)

    return middleware
