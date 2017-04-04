import json

import pytest
from django.test import Client
import requests_mock


@pytest.mark.django_db
@pytest.mark.parametrize('enable', (False, True))
@pytest.mark.parametrize('as_admin', (False, True))
@pytest.mark.parametrize('posting', (False, True))
def test_cavalry(settings, as_admin, enable, posting, django_user_model):
    settings.CAVALRY_ENABLED = enable
    settings.CAVALRY_ELASTICSEARCH_URL_TEMPLATE = ('http://localhost:59595/asdf/foo' if posting else None)
    client = Client()
    if as_admin:
        user = django_user_model.objects.create_superuser(
            username='adminator',
            email='adminator@example.com',
            password='henlo',
        )
        client.force_login(user)
    else:
        user = None
    with requests_mock.mock() as m:
        m.post(settings.CAVALRY_ELASTICSEARCH_URL_TEMPLATE, status_code=201, json={'ok': True})
        content = client.get('/').content

    # Check precondition: the user seemed logged in
    assert (b'adminator' in content) == as_admin

    # Check that the injection div only appears for admins
    assert (b'<div' in content) == (enable and as_admin)

    # Check that stats are posted only when posting is enabled
    assert bool(m.called) == (enable and posting)
    if enable and posting:
        payload = json.loads(m.request_history[-1].body.decode('utf-8'))
        # Check that user IDs are sent
        assert payload.get('user_id') == (user.id if user else None)
