from debug_toolbar.toolbar import debug_toolbar_urls
from django.contrib import admin
from django.urls import path, include

from eshop.settings import DEBUG

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("main.urls", namespace="main")),
    path("catalog/<slug:slug>", include("goods.urls", namespace="catalog"))
]

if DEBUG:
    urlpatterns = urlpatterns + debug_toolbar_urls()