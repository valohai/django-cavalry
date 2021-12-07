# django-cavalry

A Performance Tracer!

![CircleCI](https://img.shields.io/github/workflow/status/valohai/django-cavalry/build)
![Codecov](https://img.shields.io/codecov/c/github/valohai/django-cavalry.svg)
![PyPI](https://img.shields.io/pypi/v/django-cavalry.svg)
![MIT License](https://img.shields.io/github/license/valohai/django-cavalry.svg)


## Setup

* Add `'cavalry.middleware.cavalry'` to your middleware.
* Add `CAVALRY_ENABLED = bool(DEBUG)` (or similar~) to your settings.

## Settings – General

### `CAVALRY_ENABLED`
(boolean, default False)

Master switch for the middleware.

This is toggleable during runtime. That is, it does not
wholesale disable the middleware forever via the `MiddlewareNotUsed` mechanism.

### `CAVALRY_PROBABILITY`
(float, default 1)

Probability (0..1) for a request to be traced; useful in production.

### `CAVALRY_DB_RECORD_STACKS`
(boolean, default True)

Whether or not database stack traces should be recorded.
Recording stack traces naturally has a performance impact.

## Settings – Posting

The `requests` library must be available for posting to work.

You can install it by hand, or by using the `[poster]` extra while installing Cavalry.

### `CAVALRY_ELASTICSEARCH_URL_TEMPLATE`
(string)

An URL template for posting payloads to Elasticsearch.
`{curly-braced}` segments are interpolated using Python syntax.
All fields in the payload are available, plus `{ymd}` is the `YYYY-MM-DD` of the current time.
If falsy, no Elasticsearch posting is attempted.

An useful default might be `'http://localhost:9200/my-app-{ymd}/item'`. This is easily ingestible by Kibana.

### `CAVALRY_THREADED_POST`

(boolean, default False)

Whether or not to execute posting in another thread.

Enabling this has a positive performance impact in that formatting and submitting data to Elasticsearch data
will not tie up request handling.

On the flipside, though, if the worker process dies before posting is complete, the trace is lost.

Also, if you're running on uWSGI, make sure `enable-threads` is set.

### `CAVALRY_POST_STACKS`

(boolean, default True)

Whether or not post stack traces.

Not posting stack traces makes the ES payloads smaller.

## Runtime

When running in `DEBUG`, or when you're a superuser, Cavalry injects a small perf bar
into each rendered HTML page, as well as a script segment that outputs SQL queries into the dev console.

By default, stack traces are not printed for the SQL queries; add the `_cavalry_stacks` query parameter to have
them printed too.
