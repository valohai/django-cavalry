import json

import pytest
import requests_mock
from django.http import HttpResponse, StreamingHttpResponse
from django.test import Client


def assert_response_content(
    resp: HttpResponse,
    content: bytes,
    *,
    should_expose_info: bool,
    should_have_html: bool,
) -> None:
    assert (b"<div" in content) == should_have_html
    # Check the header is present when it should be, and is parseable
    assert ("x-cavalry-data" in resp) == should_expose_info
    if "x-cavalry-data" in resp:
        assert json.loads(resp["x-cavalry-data"])


@pytest.mark.django_db
@pytest.mark.parametrize("enable", [False, True], ids=("disabled", "enabled"))
@pytest.mark.parametrize("as_admin", [False, True], ids=("as_user", "as_admin"))
@pytest.mark.parametrize("posting", [False, True], ids=("nopost", "posting"))
@pytest.mark.parametrize("streaming", [False, True], ids=("regular", "streaming"))
def test_cavalry(settings, as_admin, enable, posting, admin_user, streaming):
    settings.CAVALRY_ENABLED = enable
    settings.CAVALRY_ELASTICSEARCH_URL_TEMPLATE = "http://localhost:59595/asdf/foo" if posting else None
    client = Client()
    if as_admin:
        user = admin_user
        client.force_login(user)
    else:
        user = None
    with requests_mock.mock() as m:
        m.post(
            settings.CAVALRY_ELASTICSEARCH_URL_TEMPLATE,
            status_code=201,
            json={"ok": True},
        )
        resp = client.get("/streaming/" if streaming else "/")
        if isinstance(resp, StreamingHttpResponse):
            content = resp.getvalue()
        else:
            content = resp.content

    # Check precondition: the user seemed logged in
    assert (f"Henlo {admin_user.username}".encode() in content) == as_admin

    # Check that the injection div/header only appears for admins and when not streaming
    assert_response_content(
        resp,
        content,
        should_expose_info=(enable and as_admin),
        should_have_html=(enable and as_admin and not streaming),
    )

    # Check that stats are posted only when posting is enabled
    assert bool(m.called) == (enable and posting)
    if enable and posting:
        payload = json.loads(m.request_history[-1].body.decode("utf-8"))
        # Check that user IDs are sent
        assert payload.get("user_id") == (user.id if user else None)
        database_info = payload["databases"]["default"]
        if database_info["n_queries"]:
            assert database_info["time"] > 0


@pytest.mark.django_db
@pytest.mark.parametrize("arg", ["", "?plsplspls=1"])
def test_can_inject_stats_override(settings, client, arg):
    """
    Test that a view (or a middleware) can enable stats injection
    despite the user not being a superuser, or DEBUG being off.
    """
    settings.CAVALRY_ENABLED = True
    settings.DEBUG = False
    resp = client.get(f"/overrider/{arg}")
    assert_response_content(
        resp,
        resp.content,
        should_expose_info=bool(arg),
        should_have_html=bool(arg),
    )
