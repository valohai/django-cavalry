import json
from typing import List

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.utils.crypto import get_random_string

from cavalry.policy import can_report_stacks
from cavalry.stack import Stack

STYLE = '''
#cv {
position:fixed;
z-index:9999;
bottom:0;
left:50%;
transform: translateX(-50%);
text-align:center;
font:10px/1.1 menlo,consolas,monospace;
background:rgba(0,0,0,0.8);
color:#fff;
padding:1px;
}
'''.replace('\n', '').strip()


def inject_html(request: WSGIRequest, response: HttpResponse, data: dict, summary_data: dict) -> None:
    try:
        body_closing_index = response.content.rindex(b'</body>')
    except ValueError:
        return
    content = ' | '.join(
        '%s=%s' % (key, round(value, 3) if isinstance(value, float) else value)
        for (key, value)
        in sorted(summary_data.items())
    )
    ns = 'cv_%s' % get_random_string()
    html = """<style>{style}</style><div id="{ns}">{content}</div>""".format(
        ns=ns,
        content=content,
        style=STYLE.replace('#cv', '#' + ns),
    )
    script = generate_console_script(data, with_stacks=can_report_stacks(request))
    html += "<script>{script}</script>".format(script='\n'.join(script))

    response.content = (
        response.content[:body_closing_index] +
        html.encode('utf-8') +
        response.content[body_closing_index:]
    )

    if 'content-length' in response:
        response['content-length'] = len(response.content)


def generate_console_script(data: dict, with_stacks: bool = False) -> List[str]:
    script = []
    for db, data in data.get('databases', {}).items():
        queries = data['queries']
        header = '{db}: {n} queries ({t} msec)'.format(
            db=db,
            n=data['n_queries'],
            t=data['time'],
        )
        script.append('console.group({});'.format(json.dumps(header)))
        for query in queries:
            stack = (query.get('stack', None) if with_stacks else ())
            script.append('console.log({time:.3f}, {sql});'.format(
                time=query.get('hrtime', 0) * 1000, sql=json.dumps(query['sql'])))
            if stack:
                script.append('console.groupCollapsed("Stack");')
                stack_lines = stack.as_lines()
                script.append('console.log({});'.format(json.dumps('\n'.join(stack_lines))))
                script.append('console.groupEnd();')

        script.append('console.groupEnd();')
    return script


def inject_stats(request: WSGIRequest, response: HttpResponse, data: dict) -> None:
    summary_data = summarize_data(data)
    content_type = response.get('content-type', '').lower()
    if content_type.startswith('text/html') and ('charset' not in content_type or 'utf-8' in content_type):
        inject_html(request, response, data, summary_data)
    response['x-cavalry-data'] = json.dumps(summary_data)


def summarize_data(data: dict) -> dict:
    summary_data = {
        'request time': data['duration'] * 1000,
    }
    for db, db_data in data.get('databases', {}).items():
        summary_data['queries [%s]' % db] = db_data['n_queries']
        summary_data['time [%s]' % db] = db_data['time']
    return summary_data
