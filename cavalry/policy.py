from random import random

from django.conf import settings


def get_request_es_url_template(request):
    return getattr(settings, 'CAVALRY_ELASTICSEARCH_URL_TEMPLATE', None)


def can_cavalrize(request):
    if not getattr(settings, 'CAVALRY_ENABLED', False):
        return False
    probability = getattr(settings, 'CAVALRY_PROBABILITY', 1.0)
    return probability >= 1 or (random() < probability)


def can_post_stats(request):
    return bool(get_request_es_url_template(request))


def can_record_stacks(request):
    # By default, only record stacks if we're
    # allowed to and going to use them for posting or reporting.
    if getattr(settings, 'CAVALRY_DB_RECORD_STACKS', True):
        return (can_post_stats(request) or can_report_stacks(request))
    return False


def can_serialize_stacks(request):
    # NB: request will always be None here
    return getattr(settings, 'CAVALRY_POST_STACKS', True)


def can_report_stacks(request):
    return bool(request.GET.get('_cavalry_stacks'))


def can_inject_stats(request):
    # When debugging, stats can always be shown
    if settings.DEBUG:
        return True

    # When the user (if there is one) is a superuser, stats can be shown
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_superuser', False):
        return True

    return False


def can_post_threaded(request):
    return getattr(settings, 'CAVALRY_THREADED_POST', False)
