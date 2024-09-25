from django.contrib import admin
from django.http import StreamingHttpResponse
from django.template.loader import render_to_string
from django.urls import path
from django.views.generic import TemplateView

regular_view = TemplateView.as_view(template_name="index.html")


def streaming_view(request):
    content = render_to_string("index.html", request=request)
    return StreamingHttpResponse(iter(content), content_type="text/html")


def overrider_view(request):
    """
    A view that sets the override flag for stats injection.
    """
    assert not request.user.is_superuser
    request._cavalry_can_inject_stats = bool(request.GET.get("plsplspls"))
    return regular_view(request)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", regular_view),
    path("streaming/", streaming_view),
    path("overrider/", overrider_view),
]
