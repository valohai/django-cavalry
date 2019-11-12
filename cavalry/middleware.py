from threading import Thread

from django.db import connections
from django.template.response import SimpleTemplateResponse

from cavalry.db import force_debug_cursor, patch_db
from cavalry.locals import managed
from cavalry.policy import can_cavalrize, can_inject_stats, can_post_stats, can_post_threaded, can_record_stacks
from cavalry.poster import post_stats
from cavalry.reporter import inject_stats
from cavalry.timing import get_time


def _process(request, get_response):
    with force_debug_cursor(), managed(
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
            queries = conn.queries
            data['databases'][conn.alias] = {
                'queries': queries,
                'n_queries': len(queries),
                'time': (sum(q.get('hrtime', 0) * 1000 for q in queries) if queries else 0),
            }

    if can_inject_stats(request):
        inject_stats(request, response, data)

    if can_post_stats(request):
        post_stats_kwargs = {'request': request, 'response': response, 'data': data}
        if can_post_threaded(request):
            Thread(name='cavalry poster', target=post_stats, kwargs=post_stats_kwargs, daemon=False).start()
        else:
            post_stats(**post_stats_kwargs)

    return response


def cavalry(get_response):
    patch_db()

    def middleware(request):
        if not can_cavalrize(request):
            return get_response(request)
        return _process(request, get_response)

    return middleware
