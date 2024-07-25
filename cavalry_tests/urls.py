from django.contrib import admin
from django.http import StreamingHttpResponse
from django.template.loader import render_to_string
from django.urls import path
from django.views.generic import TemplateView


def streaming_view(request):
    content = render_to_string("index.html", request=request)
    return StreamingHttpResponse(iter(content), content_type="text/html")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="index.html")),
    path("streaming/", streaming_view),
]
